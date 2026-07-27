"""数据业务服务 - AkShare 数据源实现

将原 Tsanghi 数据源替换为免费的 AkShare（东方财富/新浪公开行情）。
保持对外方法签名与返回结构与原实现一致，因此上层服务（分析、回测）无需改动。

支持市场：
- CHN：A股 / ETF（主力，AkShare 覆盖最完整）
- 其它市场暂以 A 股逻辑兜底
"""

import os
import json
import time
import threading
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional

import akshare as ak

from app.algorithms.backtest.models import KBar
from app.utils.helper import parse_otc_marker
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# 为 akshare 底层的 requests 调用注入默认超时
# ---------------------------------------------------------------------------
# akshare 多数接口调用 requests 时不传 timeout，遇到网络异常会无限阻塞，
# 进而拖死线程/请求。这里给 requests.Session.request 注入一个默认超时，
# 仅影响“对外的 HTTP 请求”，不会影响 Flask/werkzeug 自身的监听 socket。
_DEFAULT_HTTP_TIMEOUT = 12  # 秒

def _patch_requests_default_timeout():
    try:
        import requests
        if getattr(requests.Session, "_default_timeout_patched", False):
            return
        _orig_request = requests.Session.request

        def _request_with_timeout(self, method, url, **kwargs):
            if kwargs.get("timeout") is None:
                kwargs["timeout"] = _DEFAULT_HTTP_TIMEOUT
            return _orig_request(self, method, url, **kwargs)

        requests.Session.request = _request_with_timeout
        requests.Session._default_timeout_patched = True
        logger.info(f"已为 requests 注入默认超时 {_DEFAULT_HTTP_TIMEOUT}s")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"注入 requests 默认超时失败: {e}")

_patch_requests_default_timeout()


# 简单的进程内缓存（带 TTL），减少对外部接口的重复请求
_CACHE_LOCK = threading.Lock()
_CACHE = {}

# 名称表磁盘缓存目录（避免每次重启都重新下载全量名称表，~15s）
_DISK_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cache")
_DISK_CACHE_TTL = 7 * 86400  # 7天


def _disk_cache_load(name: str):
    """从磁盘读取名称表缓存（dict）。过期或不存在返回 None。"""
    try:
        path = os.path.join(_DISK_CACHE_DIR, f"{name}.json")
        if not os.path.exists(path):
            return None
        if time.time() - os.path.getmtime(path) > _DISK_CACHE_TTL:
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return None


def _disk_cache_save(name: str, data: dict):
    """将名称表缓存写入磁盘。"""
    try:
        os.makedirs(_DISK_CACHE_DIR, exist_ok=True)
        path = os.path.join(_DISK_CACHE_DIR, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"写入磁盘缓存失败 {name}: {e}")


def _cache_get(key: str):
    with _CACHE_LOCK:
        item = _CACHE.get(key)
        if not item:
            return None
        value, expire_at = item
        if expire_at is not None and time.time() > expire_at:
            _CACHE.pop(key, None)
            return None
        return value


def _cache_set(key: str, value, ttl: Optional[int] = None):
    with _CACHE_LOCK:
        expire_at = (time.time() + ttl) if ttl else None
        _CACHE[key] = (value, expire_at)


def _retry(func, *args, retries: int = 4, delay: float = 1.5, **kwargs):
    """对 AkShare 调用做带退避的重试，缓解 eastmoney 偶发的连接重置/限流。"""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:  # noqa: BLE001
            last_err = e
            logger.warning(f"AkShare 调用失败({func.__name__}) 第{attempt}次: {e}")
            if attempt < retries:
                time.sleep(delay * attempt)
    raise last_err


# 常见 ETF 名称内置映射（避免为取名而下载整张 ETF 行情表，从而触发限流）
_ETF_NAME_MAP = {
    "510300": "沪深300ETF", "510500": "中证500ETF", "159919": "沪深300ETF",
    "159915": "创业板ETF", "512880": "证券ETF", "515050": "5G通信ETF",
    "512690": "酒ETF", "516160": "新能源ETF", "159928": "消费ETF",
    "512170": "医疗ETF", "159941": "纳指ETF", "513100": "纳指ETF",
    "159920": "恒生ETF", "510880": "红利ETF", "588000": "科创50ETF",
    "512480": "半导体ETF", "159819": "人工智能ETF", "159742": "恒生科技ETF",
    "159949": "创业板50ETF", "510050": "上证50ETF", "512100": "中证1000ETF",
    "513050": "中概互联网ETF", "513180": "恒生科技指数ETF", "518880": "黄金ETF",
    # LOF（名称表多不含，内置补充）
    "161226": "白银LOF", "501018": "南方原油LOF",
    "162411": "华宝油气LOF", "161127": "标普生物科技LOF", "164824": "印度LOF",
    # 指数（候选池中的宽基指数，便于名称显示）
    "000300": "沪深300指数", "000905": "中证500指数", "000016": "上证50指数",
    "399006": "创业板指", "000688": "科创50指数", "000852": "中证1000指数",
    "399673": "创业板50指数", "899050": "北证50指数",
}


def _sina_symbol(code: str, exchange: str) -> str:
    """转换为 Sina 行情符号，如 sh510300 / sz159915。"""
    prefix = "sh" if exchange == "XSHG" else "sz"
    return f"{prefix}{code}"


# 内置指数代码表：code -> (sina_symbol, name)
# 指数代码与深市个股(000xxx)会冲突，故用白名单精确识别常见宽基/主题指数。
_INDEX_MAP = {
    "000688": ("sh000688", "科创50指数"),
    "000300": ("sh000300", "沪深300指数"),
    "000905": ("sh000905", "中证500指数"),
    "000852": ("sh000852", "中证1000指数"),
    "000016": ("sh000016", "上证50指数"),
    "000001": ("sh000001", "上证指数"),
    "000922": ("sh000922", "中证红利指数"),
    "000985": ("sh000985", "中证全指"),
    "000010": ("sh000010", "上证180指数"),
    "399001": ("sz399001", "深证成指"),
    "399006": ("sz399006", "创业板指"),
    "399005": ("sz399005", "中小板指"),
    "399300": ("sz399300", "沪深300指数(深)"),
    "399673": ("sz399673", "创业板50指数"),
    "932000": ("sh932000", "中证2000指数"),
    "899050": ("bj899050", "北证50指数"),
}


def _is_index(code: str) -> bool:
    return str(code).strip() in _INDEX_MAP


def _index_sina_symbol(code: str) -> str:
    return _INDEX_MAP[str(code).strip()][0]


def _index_name(code: str) -> str:
    return _INDEX_MAP[str(code).strip()][1]


def _get_etf_name_table() -> dict:
    """新浪 ETF 分类表 code(纯数字)->name，带内存+磁盘长缓存。"""
    cache_key = "table:etf_names"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    # 磁盘缓存（跨重启复用，避免每次启动重新下载）
    disk = _disk_cache_load("etf_names")
    if disk:
        _cache_set(cache_key, disk, ttl=86400)
        return disk
    table = {}
    try:
        df = _retry(ak.fund_etf_category_sina, symbol="ETF基金", retries=2, delay=1.0)
        for _, row in df.iterrows():
            raw = str(row["代码"])  # 形如 sh510300 / sz159915
            digits = raw[2:] if raw[:2] in ("sh", "sz") else raw
            table[digits] = str(row["名称"])
    except Exception as e:  # noqa: BLE001
        logger.warning(f"加载 ETF 名称表失败: {e}")
    if table:
        _cache_set(cache_key, table, ttl=86400)
        _disk_cache_save("etf_names", table)
    return table


def _get_stock_name_table() -> dict:
    """全量 A 股 code->name 表，带内存+磁盘长缓存与多源兜底。"""
    cache_key = "table:stock_names"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    # 磁盘缓存（跨重启复用，省去每次启动 ~15s 的全量下载）
    disk = _disk_cache_load("stock_names")
    if disk:
        _cache_set(cache_key, disk, ttl=86400)
        return disk
    table = {}
    try:
        df = _retry(ak.stock_info_a_code_name, retries=2, delay=1.0)
        # 列通常为 ['code', 'name']
        code_col = "code" if "code" in df.columns else df.columns[0]
        name_col = "name" if "name" in df.columns else df.columns[1]
        for _, row in df.iterrows():
            table[str(row[code_col])] = str(row[name_col])
    except Exception as e:  # noqa: BLE001
        logger.warning(f"加载个股名称表失败: {e}")
    if table:
        _cache_set(cache_key, table, ttl=86400)
        _disk_cache_save("stock_names", table)
    return table


def _get_fund_name_table() -> dict:
    """全量场外(开放式)基金 code->简称 表，带内存+磁盘长缓存。

    数据源：东方财富 `fund_name_em`（约 2.7 万只，首次下载较慢），
    与个股名称表策略一致：磁盘长缓存跨重启复用，失败则兜底显示代码。
    """
    cache_key = "table:fund_names"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    disk = _disk_cache_load("fund_names")
    if disk:
        _cache_set(cache_key, disk, ttl=86400)
        return disk
    table = {}
    try:
        df = _retry(ak.fund_name_em, retries=2, delay=1.0)
        # 列通常为 ['基金代码', '拼音缩写', '基金简称', '基金类型', '拼音全称']
        cols = df.columns.tolist()
        code_col = "基金代码" if "基金代码" in cols else cols[0]
        name_col = "基金简称" if "基金简称" in cols else (cols[2] if len(cols) > 2 else cols[-1])
        for _, row in df.iterrows():
            table[str(row[code_col]).zfill(6)] = str(row[name_col])
    except Exception as e:  # noqa: BLE001
        logger.warning(f"加载场外基金名称表失败: {e}")
    if table:
        _cache_set(cache_key, table, ttl=86400)
        _disk_cache_save("fund_names", table)
    return table


def _classify(ticker: str, country_code: str = "CHN") -> tuple[bool, str]:
    """判断证券类型与交易所代码。

    Returns:
        (is_etf, exchange_code)
        exchange_code: XSHG(上交所) / XSHE(深交所)
    """
    code = str(ticker).strip()
    # 交易所判定：6/5/9/68/11/113 开头视为上交所，其余（0/3/15/16）为深交所
    if code[:1] in ("5", "6", "9") or code[:2] in ("11", "68"):
        exchange = "XSHG"
    else:
        exchange = "XSHE"
    # ETF 判定：上交所 5 开头、深交所 15/16 开头
    is_etf = code[:1] == "5" or code[:2] in ("15", "16")
    return is_etf, exchange


def _normalize_daily(df: pd.DataFrame) -> pd.DataFrame:
    """将 AkShare 中文列名的日线数据规范为统一英文列。"""
    rename_map = {
        "日期": "date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
        "成交额": "amount",
        "涨跌幅": "change_pct",
    }
    df = df.rename(columns=rename_map)
    keep = ["date", "open", "high", "low", "close", "volume", "amount"]
    if "change_pct" in df.columns:
        keep.append("change_pct")
    df = df[[c for c in keep if c in df.columns]].copy()
    # 类型规范
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    for col in ["open", "high", "low", "close", "amount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "volume" in df.columns:
        # AkShare ETF 成交量单位为“手”，转换为“股”(×100) 以贴近真实股数口径
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    return df


class DataService:
    """数据业务服务（AkShare 实现）"""

    def __init__(self):
        # 无需 token，保留属性以兼容调用方
        self.provider = "akshare"

    # ------------------------------------------------------------------
    # 基础信息 / 搜索
    # ------------------------------------------------------------------
    def search_by_ticker(self, ticker: str, country_code: str = "CHN", sec_type_hint: str = ""):
        """搜索标的，返回 {code, name, exchange_code, type}。

        sec_type_hint='FUND' 或代码带场外基金标记(F/O)时，识别为场外(开放式)基金。
        """
        try:
            code = str(ticker).strip()
            # 场外基金优先识别：由标记或上层 hint 决定（其代码与场内标的冲突，需显式区分）
            clean_code, is_otc = parse_otc_marker(code)
            if is_otc or sec_type_hint == "FUND":
                return {
                    "code": clean_code,
                    "name": self._lookup_fund_name(clean_code),
                    "exchange_code": "",
                    "type": "FUND",
                    "management": "",
                }
            # 指数优先识别（白名单），避免与深市个股 000xxx 冲突
            if _is_index(code):
                sym = _index_sina_symbol(code)
                exchange = "XSHG" if sym.startswith("sh") else "XSHE"
                return {
                    "code": code,
                    "name": _index_name(code),
                    "exchange_code": exchange,
                    "type": "INDEX",
                    "management": "",
                }
            is_etf, exchange = _classify(code, country_code)
            sec_type = "ETF" if is_etf else "STOCK"
            name = self._lookup_name(code, is_etf)
            return {
                "code": code,
                "name": name,
                "exchange_code": exchange,
                "type": sec_type,
                "management": "",
            }
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            raise

    def _lookup_name(self, code: str, is_etf: bool) -> str:
        """获取标的名称（多源 + 缓存 + 兜底）。

        ETF：内置映射 → 新浪 ETF 分类表（稳定）。
        个股：全量 A 股 code→name 表（带缓存与重试）→ 个股信息接口。
        全部失败则兜底显示代码。
        """
        cache_key = f"name:{code}"
        cached = _cache_get(cache_key)
        if cached:
            return cached

        name = code
        try:
            if is_etf:
                # 1) 内置映射
                if code in _ETF_NAME_MAP:
                    name = _ETF_NAME_MAP[code]
                else:
                    # 2) 新浪 ETF 分类表（代码形如 sh510300 / sz159915）
                    table = _get_etf_name_table()
                    name = table.get(code, code)
            else:
                # 个股：全量 code→name 表
                table = _get_stock_name_table()
                name = table.get(code, code)
                # 兜底：单只个股信息接口
                if name == code:
                    try:
                        info = _retry(ak.stock_individual_info_em, symbol=code, retries=1, delay=0.5)
                        row = info[info["item"] == "股票简称"]
                        if len(row):
                            name = str(row.iloc[0]["value"])
                    except Exception:  # noqa: BLE001
                        pass
        except Exception as e:  # noqa: BLE001
            logger.warning(f"名称查询失败，使用代码兜底: {code}, {e}")

        if name and name != code:
            _cache_set(cache_key, name, ttl=86400)
        return name

    def _lookup_fund_name(self, code: str) -> str:
        """获取场外基金名称（名称表 + 缓存 + 兜底）。查不到则显示 场外基金{code}。"""
        cache_key = f"fundname:{code}"
        cached = _cache_get(cache_key)
        if cached:
            return cached
        name = None
        try:
            table = _get_fund_name_table()
            name = table.get(code) or table.get(str(code).zfill(6))
        except Exception as e:  # noqa: BLE001
            logger.warning(f"场外基金名称查询失败: {code}, {e}")
        if not name:
            name = f"场外基金{code}"
        else:
            _cache_set(cache_key, name, ttl=86400)
        return name

    def get_latest_price(self, ticker: str, exchange_code: str, type: str = "STOCK"):
        """获取最新价格信息。

        为规避实时接口偶发不稳定，统一以最近一根日线作为“最新价”，
        并使用日线自带的涨跌幅，保证稳定可用。
        """
        try:
            code = str(ticker).strip()
            end = datetime.now().strftime("%Y%m%d")
            start = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            df = self._fetch_daily(code, type, start, end)
            if df is None or len(df) == 0:
                return None
            last = df.iloc[-1]
            change_pct = None
            if "change_pct" in df.columns and pd.notna(last.get("change_pct")):
                try:
                    change_pct = round(float(last["change_pct"]), 3)
                except (ValueError, TypeError):
                    change_pct = None
            latest_dt = datetime.strptime(str(last["date"]), "%Y-%m-%d")
            data_age_days = (datetime.now() - latest_dt).days
            return {
                "close": float(last["close"]),
                "open": float(last["open"]),
                "high": float(last["high"]),
                "low": float(last["low"]),
                "volume": int(last["volume"]) if pd.notna(last["volume"]) else 0,
                "amount": float(last["amount"]) if pd.notna(last.get("amount")) else 0,
                "date": str(last["date"]),
                "change_pct": change_pct,
                "data_age_days": data_age_days,
            }
        except Exception as e:
            logger.error(f"获取最新价格失败: {e}")
            raise

    # ------------------------------------------------------------------
    # 历史日线
    # ------------------------------------------------------------------
    def get_daily_data(self, ticker: str, exchange_code: str, type: str = "STOCK",
                       start_date: str = "", end_date: str = ""):
        """获取历史日线，返回与原实现一致的 DataFrame。"""
        try:
            code = str(ticker).strip()
            start = self._to_compact_date(start_date) or (datetime.now() - timedelta(days=400)).strftime("%Y%m%d")
            end = self._to_compact_date(end_date) or datetime.now().strftime("%Y%m%d")
            df = self._fetch_daily(code, type, start, end)
            if df is None or len(df) == 0:
                return None
            # 补全 amount（理论上 AkShare 已含成交额）
            if "amount" not in df.columns:
                df["amount"] = ((df["open"] + df["close"] + df["high"] + df["low"]) / 4) * df["volume"]
            return df
        except Exception as e:
            logger.error(f"获取行情失败: {e}")
            raise

    def _fetch_daily(self, code: str, sec_type: str, start_compact: str, end_compact: str) -> Optional[pd.DataFrame]:
        """获取指定区间日线：从"全量历史缓存"切片，避免重复下载整段历史。"""
        full = self._get_full_history(code, sec_type)
        if full is None or len(full) == 0:
            return None

        start_d = f"{start_compact[:4]}-{start_compact[4:6]}-{start_compact[6:]}" if start_compact else None
        end_d = f"{end_compact[:4]}-{end_compact[4:6]}-{end_compact[6:]}" if end_compact else None

        df = full
        if start_d:
            df = df[df["date"] >= start_d]
        if end_d:
            df = df[df["date"] <= end_d]
        return df.reset_index(drop=True)

    def _get_full_history(self, code: str, sec_type: str) -> Optional[pd.DataFrame]:
        """获取并缓存标的的全量日线历史（按 code 缓存，多次区间请求复用）。

        新浪接口本身返回全量历史，这里只下载一次、长缓存，后续按区间在内存切片，
        从而消除单次分析中的重复网络请求（最新价/历史/回测共用同一份数据）。
        """
        cache_key = f"full:qfq:{sec_type}:{code}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        # 场外基金：走开放式基金净值接口，单独处理并直接返回
        if sec_type == "FUND":
            df = self._fetch_full_open_fund(code)
            if df is None or len(df) == 0:
                return None
            df = df.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)
            _cache_set(cache_key, df, ttl=3600)
            return df

        # 主源：新浪(sina) — 一次返回全量历史，稳定快速
        df = self._fetch_full_sina(code, sec_type)

        # 兜底源：东方财富(eastmoney) — 取近 ~13 年覆盖常见需求
        if (df is None or len(df) == 0) and sec_type != "INDEX":
            try:
                start_compact = "20130101"
                end_compact = datetime.now().strftime("%Y%m%d")
                if sec_type == "ETF":
                    raw = _retry(ak.fund_etf_hist_em, symbol=code, period="daily",
                                 start_date=start_compact, end_date=end_compact, adjust="qfq",
                                 retries=2, delay=1.0)
                else:
                    raw = _retry(ak.stock_zh_a_hist, symbol=code, period="daily",
                                 start_date=start_compact, end_date=end_compact, adjust="qfq",
                                 retries=2, delay=1.0)
                if raw is not None and len(raw):
                    df = _normalize_daily(raw)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"东方财富全量历史兜底也失败: {code}, {e}")
        # 指数兜底：东财指数接口
        elif (df is None or len(df) == 0) and sec_type == "INDEX":
            try:
                raw = _retry(ak.index_zh_a_hist, symbol=code, period="daily",
                             start_date="20100101", end_date=datetime.now().strftime("%Y%m%d"),
                             retries=2, delay=1.0)
                if raw is not None and len(raw):
                    df = _normalize_daily(raw)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"东方财富指数兜底也失败: {code}, {e}")

        if df is None or len(df) == 0:
            return None
        df = df.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)
        # 当日收盘后数据稳定，缓存 1 小时即可
        _cache_set(cache_key, df, ttl=3600)
        return df

    def _fetch_full_open_fund(self, code: str) -> Optional[pd.DataFrame]:
        """场外(开放式)基金全量净值序列，统一为日线字段。

        数据源：东方财富 `fund_open_fund_info_em`（单位净值走势）。
        场外基金每个交易日仅有一个「单位净值」，故 open/high/low/close 均用净值填充，
        volume=0（净值申赎无盘中成交量）。这样上层回测/均线引擎可无差别复用。
        """
        try:
            raw = _retry(ak.fund_open_fund_info_em, symbol=code,
                         indicator="单位净值走势", retries=3, delay=1.5)
            if raw is None or len(raw) == 0:
                return None
            # 列：净值日期 / 单位净值 / 日增长率
            date_col = "净值日期" if "净值日期" in raw.columns else raw.columns[0]
            nav_col = "单位净值" if "单位净值" in raw.columns else raw.columns[1]
            nav = pd.to_numeric(raw[nav_col], errors="coerce")
            df = pd.DataFrame({
                "date": pd.to_datetime(raw[date_col]).dt.strftime("%Y-%m-%d"),
                "open": nav.values,
                "high": nav.values,
                "low": nav.values,
                "close": nav.values,
                "volume": 0,
            })
            df["amount"] = 0.0
            df = df.dropna(subset=["close"]).sort_values("date").reset_index(drop=True)
            return df
        except Exception as e:  # noqa: BLE001
            logger.error(f"场外基金净值获取失败: {code}, {e}")
            return None

    def _fetch_full_sina(self, code: str, sec_type: str) -> Optional[pd.DataFrame]:
        """新浪全量日线，统一字段（不做区间过滤）。

        个股使用前复权(qfq)，消除分红送转导致的价格跳变（与主流回测口径一致）。
        ETF 的新浪接口不支持复权参数，保持原样（ETF 复权影响很小）。
        指数(INDEX)使用 stock_zh_index_daily。
        """
        try:
            # 指数：使用指数日线接口
            if sec_type == "INDEX" and _is_index(code):
                sym = _index_sina_symbol(code)
                raw = _retry(ak.stock_zh_index_daily, symbol=sym, retries=3, delay=1.5)
                if raw is None or len(raw) == 0:
                    return None
                df = raw[["date", "open", "high", "low", "close", "volume"]].copy()
                df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
                for col in ["open", "high", "low", "close", "volume"]:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                df["amount"] = ((df["open"] + df["close"] + df["high"] + df["low"]) / 4) * df["volume"]
                return df.reset_index(drop=True)

            _, exchange = _classify(code)
            sym = _sina_symbol(code, exchange)
            if sec_type == "ETF":
                raw = _retry(ak.fund_etf_hist_sina, symbol=sym, retries=3, delay=1.5)
            else:
                raw = _retry(ak.stock_zh_a_daily, symbol=sym, adjust="qfq", retries=3, delay=1.5)
            if raw is None or len(raw) == 0:
                return None
            raw = raw.rename(columns={
                "date": "date", "open": "open", "high": "high",
                "low": "low", "close": "close", "volume": "volume",
            })
            df = raw[["date", "open", "high", "low", "close", "volume"]].copy()
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            # 成交额：新浪无成交额，按均价估算
            df["amount"] = ((df["open"] + df["close"] + df["high"] + df["low"]) / 4) * df["volume"]
            return df.reset_index(drop=True)
        except Exception as e:  # noqa: BLE001
            logger.error(f"新浪全量历史获取失败: {code}, {e}")
            return None

    # ------------------------------------------------------------------
    # 5 分钟 K 线（回测用）
    # ------------------------------------------------------------------
    def get_5min_kline(self, ticker: str, exchange_code: str,
                       start_date: str, end_date: str, type: str = "STOCK") -> List[KBar]:
        try:
            code = str(ticker).strip()

            # 场外基金没有分钟/盘中数据，每日仅一个净值点，直接用日线净值作为回测K线
            if type == "FUND":
                logger.info(f"场外基金使用日线净值作为回测K线: {code} {start_date}~{end_date}")
                return self._daily_as_kbars(code, type, start_date, end_date)

            # 长周期（>120天）直接用日线，避免分钟数据量过大导致卡顿/超时
            try:
                span_days = (datetime.strptime(end_date, "%Y-%m-%d")
                             - datetime.strptime(start_date, "%Y-%m-%d")).days
            except Exception:  # noqa: BLE001
                span_days = 0
            if span_days > 120:
                logger.info(f"回测跨度{span_days}天(>120)，使用日线K线: {code} {start_date}~{end_date}")
                return self._daily_as_kbars(code, type, start_date, end_date)

            # em 分钟接口使用 'YYYY-MM-DD HH:MM:SS'
            start_dt = f"{start_date} 09:30:00"
            end_dt = f"{end_date} 15:00:00"
            raw = None
            try:
                if type == "ETF":
                    raw = _retry(ak.fund_etf_hist_min_em, symbol=code, period="5",
                                 start_date=start_dt, end_date=end_dt, adjust="",
                                 retries=1, delay=0.5)
                else:
                    raw = _retry(ak.stock_zh_a_hist_min_em, symbol=code, period="5",
                                 start_date=start_dt, end_date=end_dt, adjust="",
                                 retries=1, delay=0.5)
            except Exception as e:  # noqa: BLE001
                logger.info(f"5分钟K线不可用，自动回退为日线回测: {code}")

            if raw is None or len(raw) == 0:
                # 兜底：用日线作为回测 K 线（引擎按 bar 顺序处理，粒度可替换）
                logger.info(f"使用日线兜底进行回测: {code} {start_date}~{end_date}")
                return self._daily_as_kbars(code, type, start_date, end_date)

            rename_map = {
                "时间": "time", "开盘": "open", "收盘": "close",
                "最高": "high", "最低": "low", "成交量": "volume",
            }
            raw = raw.rename(columns=rename_map)

            kbars: List[KBar] = []
            for _, row in raw.iterrows():
                try:
                    t = pd.to_datetime(row["time"]).to_pydatetime()
                    kbars.append(KBar(
                        time=t,
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=int(float(row["volume"])) if pd.notna(row["volume"]) else 0,
                    ))
                except Exception:  # noqa: BLE001
                    continue
            kbars.sort(key=lambda k: k.time)
            if not kbars:
                return self._daily_as_kbars(code, type, start_date, end_date)
            return kbars
        except Exception as e:
            logger.error(f"获取5分钟K线数据失败: {e}")
            raise

    def _daily_as_kbars(self, code: str, sec_type: str, start_date: str, end_date: str) -> List[KBar]:
        """将日线数据转换为 KBar 列表，作为分钟数据不可用时的回测兜底。"""
        start = self._to_compact_date(start_date)
        end = self._to_compact_date(end_date)
        df = self._fetch_daily(code, sec_type, start, end)
        if df is None or len(df) == 0:
            return []
        kbars: List[KBar] = []
        for _, row in df.iterrows():
            try:
                t = datetime.strptime(str(row["date"]), "%Y-%m-%d")
                # 收盘时间点 15:00，贴近真实交易日结束
                t = t.replace(hour=15, minute=0, second=0)
                kbars.append(KBar(
                    time=t,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=int(row["volume"]) if pd.notna(row["volume"]) else 0,
                ))
            except Exception:  # noqa: BLE001
                continue
        kbars.sort(key=lambda k: k.time)
        return kbars

    # ------------------------------------------------------------------
    # 交易日历
    # ------------------------------------------------------------------
    def get_trading_calendar(self, exchange_code: str, limit: int = 5,
                             start_date: str = None, end_date: str = None) -> List[str]:
        """返回交易日列表（降序，最新在前），与原实现顺序一致。"""
        try:
            cache_key = "calendar:cn"
            cal = _cache_get(cache_key)
            if cal is None:
                df = _retry(ak.tool_trade_date_hist_sina)
                cal = pd.to_datetime(df["trade_date"]).dt.strftime("%Y-%m-%d").tolist()
                _cache_set(cache_key, cal, ttl=86400)

            today = datetime.now().strftime("%Y-%m-%d")
            # 仅保留不晚于今天的交易日
            past = [d for d in cal if d <= today]

            if start_date and end_date:
                rng = [d for d in past if start_date <= d <= end_date]
                rng.sort(reverse=True)
                return rng
            # 取最近 limit 个交易日，降序
            past.sort(reverse=True)
            return past[:limit]
        except Exception as e:
            logger.error(f"获取交易日历失败: {e}")
            raise

    # ------------------------------------------------------------------
    # 兼容方法
    # ------------------------------------------------------------------
    def clear_cache(self):
        try:
            with _CACHE_LOCK:
                _CACHE.clear()
            logger.info("缓存清除完成")
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
            raise

    def get_cache_stats(self) -> dict:
        with _CACHE_LOCK:
            return {"entries": len(_CACHE), "provider": "akshare"}

    @staticmethod
    def _to_compact_date(value: str) -> str:
        """将 'YYYY-MM-DD' 转为 'YYYYMMDD'；空值返回空串。"""
        if not value:
            return ""
        try:
            return datetime.strptime(value, "%Y-%m-%d").strftime("%Y%m%d")
        except ValueError:
            # 已经是紧凑格式或其它
            return value.replace("-", "")

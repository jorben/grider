"""鱼盆模型服务（市场风向标）v2

以「20日均线」为临界值（可选上下浮动 buffer），判断主流指数/品种相对临界值的强弱（YES/NO），
并衍生偏离率、趋势强度、量比、区间涨幅、状态持续时间、排序变化。

定位：判断市场大势/风格强弱，非买卖信号。

多数据源（均为免费 AkShare，本机可用）：
- sina_index : A股/中证系指数  ak.stock_zh_index_daily(shxxxxxx / szxxxxxx)
- csindex    : 中证官方接口（新浪缺数据时兜底，如中证2000）ak.stock_zh_index_hist_csindex
- hk         : 港股指数        ak.stock_hk_index_daily_sina(HSI/HSTECH/HSCEI)
- us         : 美股ETF         ak.stock_us_daily(QQQ/SPY)
- sge        : 上海金交所现货   ak.spot_hist_sge(Au99.99/Ag99.99)
"""

import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import akshare as ak

from app.services.data_service import _cache_get, _cache_set
from app.algorithms.backtest.ma_engine import calculate_ma
from app.utils.logger import get_logger

logger = get_logger(__name__)

_CACHE_TTL = 1800          # 行情缓存 30 分钟
_SNAPSHOT_TTL = 86400 * 10  # 排名快照/基线保留 10 天（跨周末/节假日仍可对比上一交易日）
_MA_PERIOD = 20

# 鱼盆模型标的清单（韩/日/台 免费源取不到，已剔除；微盘股免费源无数据，已剔除）
# source/sym 决定取数方式；name 为显示名
FISH_BASIN_INDICES: List[Dict] = [
    # 宽基指数
    {"code": "000688", "name": "科创50", "source": "sina_index", "sym": "sh000688", "cat": "宽基"},
    {"code": "399006", "name": "创业板指", "source": "sina_index", "sym": "sz399006", "cat": "宽基"},
    {"code": "000852", "name": "中证1000", "source": "sina_index", "sym": "sh000852", "cat": "宽基"},
    {"code": "000905", "name": "中证500", "source": "sina_index", "sym": "sh000905", "cat": "宽基"},
    {"code": "000510", "name": "中证A500", "source": "sina_index", "sym": "sh000510", "cat": "宽基"},
    {"code": "932000", "name": "中证2000", "source": "csindex", "sym": "932000", "cat": "宽基"},
    {"code": "000300", "name": "沪深300", "source": "sina_index", "sym": "sh000300", "cat": "宽基"},
    {"code": "000016", "name": "上证50", "source": "sina_index", "sym": "sh000016", "cat": "宽基"},
    {"code": "899050", "name": "北证50", "source": "sina_index", "sym": "bj899050", "cat": "宽基"},
    # 海外（美股ETF）
    {"code": "QQQ", "name": "纳指100", "source": "us", "sym": "QQQ", "cat": "海外"},
    {"code": "SPY", "name": "标普500", "source": "us", "sym": "SPY", "cat": "海外"},
    # 港股
    {"code": "HSI", "name": "恒生指数", "source": "hk", "sym": "HSI", "cat": "港股"},
    {"code": "HSTECH", "name": "恒生科技", "source": "hk", "sym": "HSTECH", "cat": "港股"},
    {"code": "HSCEI", "name": "国企指数", "source": "hk", "sym": "HSCEI", "cat": "港股"},
    # 商品（上海金交所现货，人民币/克；趋势与伦敦金一致）
    {"code": "GC", "name": "COMEX黄金", "source": "comex", "sym": "GC", "cat": "商品"},
    {"code": "SI", "name": "COMEX白银", "source": "comex", "sym": "SI", "cat": "商品"},
]

# 板块轮动清单（行业/主题指数；同 20 日线鱼盆逻辑）。
# 图中同花顺板块(881xxx/886xxx)免费源无数据，改用最接近的中证行业指数；
# 优先 sina(快)，sina 缺数据的走中证官方接口(csindex)。
FISH_BASIN_SECTORS: List[Dict] = [
    {"code": "931865", "name": "半导体", "source": "csindex", "sym": "931865", "cat": "科技"},
    {"code": "399975", "name": "证券公司", "source": "sina_index", "sym": "sz399975", "cat": "金融"},
    {"code": "399986", "name": "中证银行", "source": "sina_index", "sym": "sz399986", "cat": "金融"},
    {"code": "000986", "name": "石油石化", "source": "sina_index", "sym": "sh000986", "cat": "周期"},
    {"code": "000813", "name": "细分化工", "source": "csindex", "sym": "000813", "cat": "周期"},
    {"code": "399967", "name": "中证军工", "source": "sina_index", "sym": "sz399967", "cat": "科技"},
    {"code": "932088", "name": "航空航天", "source": "csindex", "sym": "932088", "cat": "科技"},
    {"code": "H30590", "name": "机器人", "source": "csindex", "sym": "H30590", "cat": "科技"},
    {"code": "399395", "name": "有色金属", "source": "sina_index", "sym": "sz399395", "cat": "周期"},
    {"code": "931152", "name": "创新药", "source": "csindex", "sym": "931152", "cat": "医药"},
    {"code": "000941", "name": "新能源", "source": "csindex", "sym": "000941", "cat": "新能源"},
    {"code": "000922", "name": "中证红利", "source": "csindex", "sym": "000922", "cat": "红利"},
    {"code": "931151", "name": "光伏产业", "source": "csindex", "sym": "931151", "cat": "新能源"},
    {"code": "931775", "name": "房地产", "source": "csindex", "sym": "931775", "cat": "周期"},
    {"code": "399932", "name": "中证消费", "source": "sina_index", "sym": "sz399932", "cat": "消费"},
    {"code": "930633", "name": "中证旅游", "source": "csindex", "sym": "930633", "cat": "消费"},
    {"code": "399971", "name": "中证传媒", "source": "sina_index", "sym": "sz399971", "cat": "传媒"},
    {"code": "399998", "name": "中证煤炭", "source": "sina_index", "sym": "sz399998", "cat": "周期"},
]


def _retry(fn, *args, retries: int = 3, delay: float = 1.2, **kwargs):
    last = None
    for i in range(retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:  # noqa: BLE001
            last = e
            if i < retries - 1:
                time.sleep(delay)
    raise last


def _fetch_daily(item: Dict) -> Optional[pd.DataFrame]:
    """按标的类型取日线，返回统一列 [date(str), close(float), volume(float)] 升序。带 30 分钟缓存。"""
    source = item.get("source")
    sym = item.get("sym")
    cache_key = f"fb_daily:{source}:{sym}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return pd.DataFrame(cached)

    df = None
    try:
        if source == "sina_index":
            raw = _retry(ak.stock_zh_index_daily, symbol=sym)
            if raw is not None and len(raw):
                df = raw[["date", "close", "volume"]].copy()
        elif source == "csindex":
            raw = _retry(ak.stock_zh_index_hist_csindex, symbol=sym,
                         start_date="20180101", end_date=datetime.now().strftime("%Y%m%d"))
            if raw is not None and len(raw):
                raw = raw.rename(columns={"日期": "date", "收盘": "close", "成交量": "volume"})
                df = raw[["date", "close", "volume"]].copy()
        elif source == "hk":
            raw = _retry(ak.stock_hk_index_daily_sina, symbol=sym)
            if raw is not None and len(raw):
                vol = "volume" if "volume" in raw.columns else None
                cols = ["date", "close"] + ([vol] if vol else [])
                df = raw[cols].copy()
                if not vol:
                    df["volume"] = 0
        elif source == "us":
            raw = _retry(ak.stock_us_daily, symbol=sym)
            if raw is not None and len(raw):
                df = raw[["date", "close", "volume"]].copy()
        elif source == "sge":
            raw = _retry(ak.spot_hist_sge, symbol=sym)
            if raw is not None and len(raw):
                df = raw[["date", "close"]].copy()
                df["volume"] = 0  # 现货无成交量
        elif source == "comex":
            # 外盘期货（COMEX 黄金 GC / 白银 SI），美元计价
            raw = _retry(ak.futures_foreign_hist, symbol=sym)
            if raw is not None and len(raw):
                vol = "volume" if "volume" in raw.columns else None
                cols = ["date", "close"] + ([vol] if vol else [])
                df = raw[cols].copy()
                if not vol:
                    df["volume"] = 0
        if df is None or len(df) == 0:
            return None

        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["volume"] = pd.to_numeric(df.get("volume", 0), errors="coerce").fillna(0)
        df = df.dropna(subset=["close"]).sort_values("date").reset_index(drop=True)
        _cache_set(cache_key, df.to_dict("list"), ttl=_CACHE_TTL)
        return df
    except Exception as e:  # noqa: BLE001
        logger.warning(f"鱼盆取数失败 {item.get('code')}({source}:{sym}): {e}")
        return None


def _fetch_realtime_maps(indices: List[Dict] = None) -> Dict:
    """一次性拉取实时快照（A股指数/港股/COMEX/腾讯兜底），全清单共享。缓存 60 秒。

    返回 {'idx': {代码->(最新价,涨跌幅小数)}, 'hk': {...}, 'comex': {名称->(最新价,涨跌幅小数)}}。
    中证官方(csindex)与美股(东财)无可用实时源，不在此表，评估时自动回退收盘。
    """
    # 缓存键含腾讯代码集合，避免大盘/板块两个清单共享到不含对方 qq 数据的缓存
    qq_syms = _collect_qq_symbols(indices) if indices else []
    ck = "fb_realtime_maps:" + (",".join(sorted(qq_syms)) if qq_syms else "base")
    cached = _cache_get(ck)
    if cached is not None:
        return cached

    maps = {"idx": {}, "hk": {}, "comex": {}}
    # A股指数实时（新浪）
    try:
        df = _retry(ak.stock_zh_index_spot_sina, retries=2, delay=1.0)
        if df is not None and len(df):
            for _, r in df.iterrows():
                code = str(r.get("代码", "")).strip()
                price = pd.to_numeric(r.get("最新价"), errors="coerce")
                chg = pd.to_numeric(r.get("涨跌幅"), errors="coerce")
                if code and pd.notna(price):
                    maps["idx"][code] = (float(price), float(chg) / 100.0 if pd.notna(chg) else None)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"A股指数实时拉取失败: {e}")
    # 港股指数实时（新浪）
    try:
        df = _retry(ak.stock_hk_index_spot_sina, retries=2, delay=1.0)
        if df is not None and len(df):
            for _, r in df.iterrows():
                code = str(r.get("代码", "")).strip()
                price = pd.to_numeric(r.get("最新价"), errors="coerce")
                chg = pd.to_numeric(r.get("涨跌幅"), errors="coerce")
                if code and pd.notna(price):
                    maps["hk"][code] = (float(price), float(chg) / 100.0 if pd.notna(chg) else None)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"港股指数实时拉取失败: {e}")
    # COMEX 外盘实时
    try:
        df = _retry(ak.futures_foreign_commodity_realtime, symbol=["GC", "SI"], retries=2, delay=1.0)
        if df is not None and len(df):
            for _, r in df.iterrows():
                nm = str(r.get("名称", "")).strip()
                price = pd.to_numeric(r.get("最新价"), errors="coerce")
                chg = pd.to_numeric(r.get("涨跌幅"), errors="coerce")
                if nm and pd.notna(price):
                    # 该接口涨跌幅已是百分数值(如 0.36 表示 0.36%)
                    maps["comex"][nm] = (float(price), float(chg) / 100.0 if pd.notna(chg) else None)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"COMEX实时拉取失败: {e}")

    # 腾讯实时兜底：覆盖 sina 实时表没有、但腾讯有的 A股/北证指数
    # （如北证50、及部分 6 位中证行业指数）。93xxxx/H30xxx 策略指数腾讯无数据，自动跳过。
    try:
        if qq_syms:
            maps["qq"] = _fetch_tencent_rt(qq_syms)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"腾讯实时拉取失败: {e}")

    _cache_set(ck, maps, ttl=60)
    return maps


def _qq_symbol(item: Dict) -> Optional[str]:
    """推导腾讯行情代码。仅对腾讯支持的返回，93xxxx/H开头等返回 None。"""
    src = item.get("source")
    sym = str(item.get("sym", "")).strip()
    if src == "sina_index":
        # 已是 shxxxxxx/szxxxxxx/bjxxxxxx，腾讯同格式
        return sym if sym[:2] in ("sh", "sz", "bj") else None
    if src == "csindex":
        # 纯数字：0xxxxx->sh，3xxxxx->sz(创业/深)；899->bj；93xxxx/H30xxx 腾讯无
        if sym.isdigit() and len(sym) == 6:
            if sym.startswith("0"):
                return "sh" + sym
            if sym.startswith("3"):
                return "sz" + sym
            if sym.startswith("899"):
                return "bj" + sym
        return None
    return None


def _collect_qq_symbols(indices: List[Dict]) -> List[str]:
    seen = set()
    out = []
    for it in indices:
        # 已有 sina 实时表覆盖的(sina_index)不必再查腾讯；仅补 csindex 且腾讯支持的
        if it.get("source") != "csindex":
            continue
        qs = _qq_symbol(it)
        if qs and qs not in seen:
            seen.add(qs)
            out.append(qs)
    return out


def _fetch_tencent_rt(qq_syms: List[str]) -> Dict:
    """批量查腾讯行情，返回 {腾讯代码: (现价, 涨跌幅小数)}。字段: parts[3]=价, parts[32]=涨跌幅%。"""
    import requests
    result = {}
    if not qq_syms:
        return result
    url = "https://qt.gtimg.cn/q=" + ",".join(qq_syms)
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
    r.encoding = "gbk"
    for line in r.text.strip().split(";"):
        line = line.strip()
        if '="' not in line:
            continue
        try:
            key = line.split("=")[0].replace("v_", "").strip()
            val = line.split('"')[1]
            parts = val.split("~")
            if len(parts) > 32 and parts[3]:
                price = float(parts[3])
                chgpct = float(parts[32]) / 100.0 if parts[32] else None
                if price > 0:
                    result[key] = (price, chgpct)
        except Exception:  # noqa: BLE001
            continue
    return result


def _lookup_realtime(item: Dict, rt_maps: Dict):
    """返回 (price, change_pct) 或 None。A股指数/港股/COMEX 有实时源；csindex 走腾讯兜底。"""
    if not rt_maps:
        return None
    src = item.get("source")
    sym = item.get("sym")
    if src == "sina_index":
        hit = rt_maps.get("idx", {}).get(sym)
        if hit:
            return hit
        # sina 实时表偶尔缺某代码，再试腾讯
        qs = _qq_symbol(item)
        return rt_maps.get("qq", {}).get(qs) if qs else None
    if src == "hk":
        return rt_maps.get("hk", {}).get(sym)
    if src == "comex":
        nm = "COMEX黄金" if sym == "GC" else ("COMEX白银" if sym == "SI" else None)
        return rt_maps.get("comex", {}).get(nm) if nm else None
    if src == "csindex":
        qs = _qq_symbol(item)
        return rt_maps.get("qq", {}).get(qs) if qs else None
    return None


def _evaluate_one(item: Dict, buffer_pct: float, rt_maps: Dict = None) -> Dict:
    code = str(item.get("code", "")).strip()
    name = item.get("name", code)
    cat = item.get("cat", "")
    try:
        df = _fetch_daily(item)
        if df is None or len(df) < _MA_PERIOD + 1:
            raise ValueError("数据不足以计算20日线")

        closes = df["close"].tolist()
        dates = df["date"].tolist()
        volumes = df["volume"].tolist()

        # 实时覆盖：若能取到实时价，用其作为"今日临时收盘"参与计算
        is_realtime = False
        rt_change = None
        rt = _lookup_realtime(item, rt_maps)
        if rt is not None:
            rt_price, rt_change = rt
            today = datetime.now().strftime("%Y-%m-%d")
            if dates and dates[-1] >= today:
                closes[-1] = rt_price  # 覆盖当日
            else:
                closes.append(rt_price)  # 追加为新的一天
                dates.append(today)
                volumes.append(0)
            is_realtime = True

        ma = calculate_ma(closes, _MA_PERIOD, "SMA")
        factor = 1.0 + (buffer_pct or 0) / 100.0

        cur_close = closes[-1]
        cur_ma = ma[-1]
        if cur_ma is None:
            raise ValueError("20日线无效")
        cur_threshold = cur_ma * factor
        cur_status = "YES" if cur_close >= cur_threshold else "NO"

        if is_realtime and rt_change is not None:
            change_pct = rt_change
        else:
            change_pct = (cur_close / closes[-2] - 1) if (len(closes) >= 2 and closes[-2]) else None
        deviation = (cur_close - cur_threshold) / cur_threshold if cur_threshold else None

        # 量比 = 当日量 / 过去5日均量（现货无量则 None）
        vol_ratio = None
        if volumes[-1] and len(volumes) >= 6:
            prev5 = volumes[-6:-1]
            avg5 = sum(prev5) / len(prev5) if prev5 else 0
            if avg5 > 0:
                vol_ratio = volumes[-1] / avg5

        # 状态持续起点：最近一次状态翻转后的第一天
        status_since = dates[-1]
        since_idx = len(closes) - 1
        for i in range(len(closes) - 2, -1, -1):
            if ma[i] is None:
                break
            st = "YES" if closes[i] >= ma[i] * factor else "NO"
            if st != cur_status:
                status_since = dates[i + 1]
                since_idx = i + 1
                break
            status_since = dates[i]
            since_idx = i

        # 区间涨幅：状态起点至今
        range_pct = None
        if closes[since_idx]:
            range_pct = cur_close / closes[since_idx] - 1

        return {
            "code": code,
            "name": name,
            "category": cat,
            "change_pct": round(change_pct, 4) if change_pct is not None else None,
            "price": round(cur_close),          # 整数
            "threshold": round(cur_threshold),  # 整数
            "ma20": round(cur_ma),              # 整数
            "status": cur_status,
            "status_since": status_since,
            "deviation": round(deviation, 4) if deviation is not None else None,
            "vol_ratio": round(vol_ratio, 2) if vol_ratio is not None else None,
            "range_pct": round(range_pct, 4) if range_pct is not None else None,
            "latest_date": dates[-1],
            "is_realtime": is_realtime,
            # 数据时间：实时行用当前时刻(时分秒)，收盘行用最近收盘日期
            "data_time": (datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                          if is_realtime else dates[-1]),
            "error": None,
        }
    except Exception as e:  # noqa: BLE001
        logger.warning(f"鱼盆模型评估失败 {code}: {e}")
        return {"code": code, "name": name, "category": cat,
                "status": None, "deviation": None, "error": str(e)}


def _assign_strength_and_rankchange(results: List[Dict], prev_rank: Dict[str, int]) -> None:
    """按偏离率从高到低赋趋势强度（1=偏离率最高/最强）；并与上次排名对比给出 rank_change。"""
    valid = [r for r in results if r.get("deviation") is not None]
    valid.sort(key=lambda r: r["deviation"], reverse=True)
    for rank, r in enumerate(valid, start=1):
        r["strength"] = rank
        old = prev_rank.get(r["code"])
        # rank_change：上次排名 - 本次排名（正=名次上升）
        r["rank_change"] = (old - rank) if isinstance(old, int) else None
    for r in results:
        if r.get("deviation") is None:
            r["strength"] = None
            r["rank_change"] = None


def _market_state(results: List[Dict]) -> Dict:
    valid = [r for r in results if r.get("status") in ("YES", "NO")]
    total = len(valid)
    yes = sum(1 for r in valid if r["status"] == "YES")
    if total == 0:
        label, tone = "未知", "neutral"
    elif yes == total:
        label, tone = "牛市状态", "bull"
    elif yes == 0:
        label, tone = "熊市状态", "bear"
    else:
        label, tone = "分化/震荡", "mixed"
    return {"label": label, "tone": tone, "yes": yes, "total": total}


class FishBasinService:
    """鱼盆模型批量评估（同步 + 缓存）"""

    def evaluate(self, indices: List[Dict] = None, buffer_pct: float = 0.0,
                 force_refresh: bool = False, board: str = "index") -> Dict:
        indices = indices or FISH_BASIN_INDICES
        cache_key = f"fish_basin:{board}:{_MA_PERIOD}:{buffer_pct}:{len(indices)}"
        snap_key = f"fish_basin:rank_snapshot:{board}"
        if not force_refresh:
            cached = _cache_get(cache_key)
            if cached is not None:
                out = dict(cached)
                out["from_cache"] = True
                return out

        holder = {}

        def _worker():
            holder["payload"] = self._do_eval(indices, cache_key, snap_key, buffer_pct)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        t.join()
        return holder.get("payload") or {
            "results": [], "market_state": _market_state([]),
            "buffer_pct": buffer_pct, "ma_period": _MA_PERIOD,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "from_cache": False,
        }

    def _do_eval(self, indices: List[Dict], cache_key: str, snap_key: str, buffer_pct: float) -> Dict:
        start = time.time()
        today = datetime.now().strftime("%Y-%m-%d")

        # 排序变化基准：按"交易日"锁定，而非每次刷新覆盖。
        # cur_snap = 当日最新排名（当天刷新会更新）；baseline = 上一交易日的排名。
        # 当天所有刷新都与"上一交易日排名"对比，这样 rank_change 反映"较昨日名次升降"。
        cur_snap = _cache_get(snap_key) or {}
        baseline = _cache_get(snap_key + ":baseline") or {}
        if cur_snap.get("date") and cur_snap.get("date") != today and cur_snap.get("rank"):
            # 进入新的一天：把昨天最后的排名提升为基线
            baseline = cur_snap
            _cache_set(snap_key + ":baseline", baseline, ttl=_SNAPSHOT_TTL)
        prev_rank = baseline.get("rank", {}) if isinstance(baseline, dict) else {}

        # 预取实时快照（含腾讯兜底，全清单共享）
        rt_maps = _fetch_realtime_maps(indices)

        results: List[Dict] = []
        for item in indices:  # 串行（akshare/V8 非线程安全）
            results.append(_evaluate_one(item, buffer_pct, rt_maps))

        _assign_strength_and_rankchange(results, prev_rank)
        # 默认按趋势强度升序（1 在前），失败项置后
        results.sort(key=lambda r: (r.get("strength") is None, r.get("strength") or 9999))

        # 保存"当日最新排名"（带日期），供跨日提升为基线
        new_rank = {r["code"]: r["strength"] for r in results if r.get("strength") is not None}
        _cache_set(snap_key, {"date": today, "rank": new_rank}, ttl=_SNAPSHOT_TTL)

        rt_count = sum(1 for r in results if r.get("is_realtime"))
        payload = {
            "results": results,
            "market_state": _market_state(results),
            "buffer_pct": buffer_pct,
            "ma_period": _MA_PERIOD,
            "realtime_count": rt_count,
            "elapsed_seconds": round(time.time() - start, 1),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "from_cache": False,
        }
        # 实时模式：结果缓存缩短到 60 秒（与实时快照同步）
        _cache_set(cache_key, payload, ttl=60)
        ms = payload["market_state"]
        logger.info(f"鱼盆模型完成: {ms['yes']}/{ms['total']} YES, 实时{rt_count}项, 耗时{payload['elapsed_seconds']}s")
        return payload

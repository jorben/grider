"""TickFlow 数据提供商。

封装 `tickflow` Python SDK 与 `exchange_calendars` 离线库，
对外暴露与旧 TsanghiProvider 兼容的 ``{ 'code': 200, 'data': [...] }`` 响应结构，
并复用 ``FileCacheManager`` 做文件级缓存。

设计要点（见 ``docs/tsanghi_vs_tickflow_analysis.md``）：
- 认证：TickFlow SDK 无参构造时自动读取 ``TICKFLOW_API_KEY`` 环境变量，
  SDK 内部以 Header ``x-api-key`` 提交，因此本类不再维护 Token。
- 缓存：endpoint 配置中声明的 ``cache_ttl`` 直接作用于 ``FileCacheManager``。
- 日历：``exchange_calendars`` 离线库支持 XSHG/XSHE/XHKG/XNYS。
- 标的代码：调用方传入 TickFlow 风格符号（``510300.SH``）；
  业务层在 ``DataService`` 中负责与 ``(ticker, exchange_code)`` 互转。
"""

from __future__ import annotations

import os
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import yaml
from tickflow import TickFlow

from app.external.file_cache_manager import FileCacheManager
from app.utils.helper import is_etf_ticker
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# 内部：缓存键与默认 TTL
# ---------------------------------------------------------------------------

# 中国（A 股）使用 Asia/Shanghai 时区（UTC+8）
CN_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")
_DEFAULT_TTL = 300  # 5 分钟兜底


def _coerce_params(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """将 None / 不可哈希的入参规整为可作为缓存键的 dict。"""
    if not params:
        return {}
    coerced: Dict[str, Any] = {}
    for k, v in params.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            coerced[k] = v
        else:
            try:
                coerced[k] = json.dumps(v, sort_keys=True, default=str)
            except (TypeError, ValueError):
                coerced[k] = str(v)
    return coerced


# ---------------------------------------------------------------------------
# 主体：TickFlowProvider
# ---------------------------------------------------------------------------


class TickFlowProvider:
    """TickFlow 数据提供商。

    参数 ``symbol`` 一律使用 TickFlow 格式（``510300.SH``、``00700.HK``），
    通过 ``DataService`` 完成与 ``(ticker, exchange_code)`` 的转换。
    """

    # 全市场 universe ID 集合（用于本地搜索缓存与代码补全）
    DEFAULT_UNIVERSES = ("CN_ETF", "CN_Equity_A")

    # exchange_calendars 库使用的交易所 ID 映射
    _CALENDAR_EXCHANGE_MAP = {
        "XSHG": "XSHG", "SH": "XSHG", "SSE": "XSHG", "SS": "XSHG", "SHA": "XSHG",
        "XSHE": "XSHE", "SZ": "XSHE", "SZSE": "XSHE", "ZS": "XSHE", "SZA": "XSHE",
        "XHKG": "XHKG", "HK": "XHKG", "HKEX": "XHKG", "HKG": "XHKG",
        "XNYS": "XNYS", "US": "XNYS", "NYSE": "XNYS", "NASDAQ": "XNYS", "USA": "XNYS",
    }

    def __init__(
        self,
        config_path: str = "app/config/config.yaml",
        provider_name: str = "tickflow",
    ):
        self.provider_name = provider_name
        self.config_path = config_path
        self.config = self._load_config()
        self.cache_manager = FileCacheManager(self._get_cache_dir())

        # SDK 客户端：无参构造时从环境变量 TICKFLOW_API_KEY 读取
        api_key = os.getenv("TICKFLOW_API_KEY")
        base_url = os.getenv("TICKFLOW_BASE_URL")
        if not api_key:
            logger.warning(
                "TICKFLOW_API_KEY 未设置，TickFlow SDK 调用将使用认证失败占位 key"
            )

        sdk_kwargs: Dict[str, Any] = {}
        if base_url:
            sdk_kwargs["base_url"] = base_url
        # 若 base_url 同时存在配置文件中，则优先使用环境变量
        file_base_url = (self.config or {}).get("base_url")
        if file_base_url and not base_url:
            sdk_kwargs["base_url"] = file_base_url

        try:
            self._client: Optional[TickFlow] = TickFlow(api_key=api_key, **sdk_kwargs)
        except Exception as exc:  # pragma: no cover - 仅在 SDK 异常构造时
            logger.error("初始化 TickFlow SDK 失败: %s", exc)
            self._client = None

        # exchange_calendars 懒加载缓存
        self._calendars: Dict[str, Any] = {}

        # 标的名称内存缓存：{symbol: name}，由 _fetch_instrument_names 维护
        self._instrument_name_cache: Dict[str, str] = {}

        logger.info("TickFlowProvider 初始化完成 (provider=%s)", provider_name)

    # ------------------------------------------------------------------
    # 配置加载
    # ------------------------------------------------------------------

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                full = yaml.safe_load(f) or {}
            return (full.get("providers") or {}).get(self.provider_name, {})
        except (OSError, yaml.YAMLError) as exc:
            logger.error("加载 TickFlow 配置失败: %s", exc)
            return {}

    def _get_cache_dir(self) -> str:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                full = yaml.safe_load(f) or {}
            return (full.get("global") or {}).get("cache_dir", "cache/external_api")
        except (OSError, yaml.YAMLError):
            return "cache/external_api"

    def _endpoint_config(self, endpoint_name: str) -> Dict[str, Any]:
        endpoints = (self.config or {}).get("endpoints") or {}
        return endpoints.get(endpoint_name, {"cache_ttl": _DEFAULT_TTL})

    # ------------------------------------------------------------------
    # 客户端 / 日历访问
    # ------------------------------------------------------------------

    @property
    def client(self) -> TickFlow:
        if self._client is None:
            raise RuntimeError("TickFlow SDK 未初始化，请检查 TICKFLOW_API_KEY 配置")
        return self._client

    def _calendar_for(self, exchange_code: str) -> Any:
        """获取 exchange_calendars 中指定市场的交易日历（懒加载）。"""
        cid = self._CALENDAR_EXCHANGE_MAP.get((exchange_code or "").upper())
        if not cid:
            raise ValueError(f"不支持的交易所代码: {exchange_code}")
        if cid not in self._calendars:
            import exchange_calendars as xcals  # 延迟导入以加速启动

            self._calendars[cid] = xcals.get_calendar(cid)
        return self._calendars[cid]

    # ------------------------------------------------------------------
    # 缓存封装
    # ------------------------------------------------------------------

    def _cached_call(
        self,
        endpoint_name: str,
        params: Optional[Dict[str, Any]],
        producer,
    ) -> Dict[str, Any]:
        """统一的缓存读取 → 远端调用 → 写回流程。

        Args:
            endpoint_name: 端点名称（用作缓存子目录）
            params: 调用参数（用作缓存键）
            producer: 无参可调用对象，缓存未命中时执行并返回 dict 响应

        Returns:
            ``{ 'code': <int>, 'data': <any> }`` 形式的响应
        """
        cfg = self._endpoint_config(endpoint_name)
        ttl = int(cfg.get("cache_ttl", _DEFAULT_TTL))
        cache_params = _coerce_params(params)

        cached = self.cache_manager.get(self.provider_name, endpoint_name, cache_params)
        if cached is not None:
            logger.debug("TickFlow 缓存命中: %s.%s", self.provider_name, endpoint_name)
            return cached

        response = producer() or {"code": 500, "data": None, "message": "empty response"}

        # 仅缓存成功响应
        if response.get("code") in (200, 0):
            try:
                self.cache_manager.set(
                    self.provider_name, endpoint_name, cache_params, response, ttl
                )
            except Exception as exc:  # pragma: no cover - 缓存写入失败不致命
                logger.warning("写入 TickFlow 缓存失败: %s", exc)

        return response

    # ------------------------------------------------------------------
    # 端点：交易所 / 标的池
    # ------------------------------------------------------------------

    def get_exchange(self, country_code: str = "CHN") -> Dict[str, Any]:
        """获取交易所清单。``country_code`` 当前仅作兼容占位，未参与过滤。"""

        def _call() -> Dict[str, Any]:
            if self._client is None:
                return {"code": 500, "data": None, "message": "TickFlow SDK 未初始化"}
            try:
                items = self.client.exchanges.list()
                return {"code": 200, "data": items}
            except Exception as exc:
                logger.error("TickFlow get_exchange 失败: %s", exc)
                return {"code": 500, "data": None, "message": str(exc)}

        return self._cached_call("exchange", {"country": country_code}, _call)

    def get_universe(self, universe_id: str) -> Dict[str, Any]:
        """获取指定 universe 的标的清单。"""

        def _call() -> Dict[str, Any]:
            if self._client is None:
                return {"code": 500, "data": None, "message": "TickFlow SDK 未初始化"}
            try:
                detail = self.client.universes.get(universe_id)
                symbols = detail.get("symbols", []) if isinstance(detail, dict) else []
                return {
                    "code": 200,
                    "data": {
                        "id": detail.get("id", universe_id),
                        "name": detail.get("name", universe_id),
                        "category": detail.get("category", ""),
                        "symbols": symbols,
                    },
                }
            except Exception as exc:
                logger.error("TickFlow get_universe(%s) 失败: %s", universe_id, exc)
                return {"code": 500, "data": None, "message": str(exc)}

        cache_endpoint = "universe_etf" if universe_id == "CN_ETF" else "universe_equity_a"
        return self._cached_call(cache_endpoint, {"universe": universe_id}, _call)

    def list_universes(self) -> Dict[str, Any]:
        """列出所有 universe（通常用于调试 / 健康检查）。"""
        if self._client is None:
            return {"code": 500, "data": None, "message": "TickFlow SDK 未初始化"}
        try:
            return {"code": 200, "data": self.client.universes.list()}
        except Exception as exc:
            logger.error("TickFlow list_universes 失败: %s", exc)
            return {"code": 500, "data": None, "message": str(exc)}

    # ------------------------------------------------------------------
    # 端点：交易日历（exchange_calendars 离线库）
    # ------------------------------------------------------------------

    def get_calendar(
        self,
        exchange_code: str = "XSHG",
        limit: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """返回 ``{'code': 200, 'data': [{'date': 'YYYY-MM-DD'}, ...]}``。

        输出顺序为降序（最新日期在前），与旧 Tsanghi 接口保持一致。
        """
        try:
            cal = self._calendar_for(exchange_code)
        except ValueError:
            return {"code": 400, "data": None, "message": f"不支持的交易所: {exchange_code}"}

        today = datetime.now(CN_TZ).date()
        if start_date and end_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            sessions = cal.sessions_in_range(start_dt, end_dt)
        else:
            # 取今天往前推 limit 天作为查询窗口，确保 limit 条都能命中
            lookback_days = max(limit * 3, 60)
            start_dt = today - timedelta(days=lookback_days)
            sessions = cal.sessions_in_range(start_dt, today + timedelta(days=1))
            # 过滤掉未来还未发生的交易日
            sessions = [s for s in sessions if s.date() <= today]
            sessions = sessions[-limit:] if limit > 0 else sessions

        # 读取临时休市兜底列表
        adhoc_holidays = self._load_adhoc_holidays()
        # adhoc_holidays 中的日期应被视作休市，因此需要从结果中剔除
        adhoc_set = set(adhoc_holidays)
        sessions = [s for s in sessions if s.date().isoformat() not in adhoc_set]

        data = [{"date": s.date().isoformat()} for s in sessions]
        data.reverse()  # 降序
        return {"code": 200, "data": data}

    def _load_adhoc_holidays(self) -> List[str]:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                full = yaml.safe_load(f) or {}
            return list((full.get("global") or {}).get("adhoc_holidays", []) or [])
        except (OSError, yaml.YAMLError):
            return []

    # ------------------------------------------------------------------
    # 端点：实时行情
    # ------------------------------------------------------------------

    def get_realtime(self, symbol: str) -> Dict[str, Any]:
        """获取实时行情（股票 / ETF 通用）。"""
        return self._fetch_realtime(symbol, endpoint_name="realtime")

    # 兼容旧 Tsanghi 命名（供测试与旧代码使用）
    def get_etf_realtime(self, symbol: str) -> Dict[str, Any]:
        return self._fetch_realtime(symbol, endpoint_name="realtime")

    def get_stock_realtime(self, symbol: str) -> Dict[str, Any]:
        return self._fetch_realtime(symbol, endpoint_name="realtime")

    def _fetch_realtime(self, symbol: str, endpoint_name: str) -> Dict[str, Any]:
        symbol = (symbol or "").strip()
        if not symbol:
            return {"code": 400, "data": None, "message": "symbol 不能为空"}

        def _call() -> Dict[str, Any]:
            if self._client is None:
                return {"code": 500, "data": None, "message": "TickFlow SDK 未初始化"}
            try:
                quotes = self.client.quotes.get(symbols=[symbol])
                items = list(quotes) if quotes else []
                if not items:
                    return {"code": 404, "data": None, "message": f"未找到实时行情: {symbol}"}
                data = [self._normalize_quote(items[0])]
                return {"code": 200, "data": data}
            except Exception as exc:
                logger.error("TickFlow realtime(%s) 失败: %s", symbol, exc)
                return {"code": 500, "data": None, "message": str(exc)}

        return self._cached_call(endpoint_name, {"symbol": symbol}, _call)

    @staticmethod
    def _normalize_quote(quote: Dict[str, Any]) -> Dict[str, Any]:
        """将 TickFlow 行情 dict 标准化为与旧 Tsanghi 行式响应兼容的结构。"""
        symbol = quote.get("symbol", "")
        ticker, exchange_code = "", ""
        if "." in symbol:
            ticker, _, suffix = symbol.rpartition(".")
            suffix = suffix.upper()
            exchange_code = {
                "SH": "XSHG", "SZ": "XSHE", "HK": "XHKG", "US": "XNYS"
            }.get(suffix, suffix)

        # 时间戳（毫秒） → 'YYYY-MM-DD HH:MM:SS'（中国时区）
        ts_ms = quote.get("timestamp")
        date_str = ""
        if isinstance(ts_ms, (int, float)) and ts_ms > 0:
            try:
                date_str = (
                    datetime.fromtimestamp(ts_ms / 1000, tz=CN_TZ)
                    .strftime("%Y-%m-%d %H:%M:%S")
                )
            except (OverflowError, OSError, ValueError):
                date_str = ""

        last_price = quote.get("last_price")
        prev_close = quote.get("prev_close")
        change_pct = None
        if last_price is not None and prev_close not in (None, 0):
            try:
                change_pct = round((float(last_price) - float(prev_close)) / float(prev_close) * 100, 3)
            except (TypeError, ValueError, ZeroDivisionError):
                change_pct = None

        return {
            "symbol": symbol,
            "ticker": ticker,
            "exchange_code": exchange_code,
            "name": quote.get("name", ""),
            "date": date_str,
            "open": quote.get("open"),
            "high": quote.get("high"),
            "low": quote.get("low"),
            "close": last_price,
            "pre_close": prev_close,
            "volume": quote.get("volume"),
            "amount": quote.get("amount"),
            "change_pct": change_pct,
        }

    # ------------------------------------------------------------------
    # 端点：日线 / 5 分钟 K 线
    # ------------------------------------------------------------------

    def get_daily(
        self,
        symbol: str,
        start_date: str = "",
        end_date: str = "",
        adjust: str = "forward",
    ) -> Dict[str, Any]:
        return self._fetch_kline(symbol, "1d", "daily", start_date, end_date, adjust)

    def get_5min(
        self,
        symbol: str,
        start_date: str = "",
        end_date: str = "",
        adjust: str = "forward",
    ) -> Dict[str, Any]:
        return self._fetch_kline(symbol, "5m", "kline_5min", start_date, end_date, adjust)

    # 兼容旧命名
    def get_etf_daily(self, symbol: str, start_date: str = "", end_date: str = "", adjust: str = "forward") -> Dict[str, Any]:
        return self.get_daily(symbol, start_date, end_date, adjust)

    def get_stock_daily(self, symbol: str, start_date: str = "", end_date: str = "", adjust: str = "forward") -> Dict[str, Any]:
        return self.get_daily(symbol, start_date, end_date, adjust)

    def get_etf_5min(self, symbol: str, start_date: str = "", end_date: str = "", adjust: str = "forward") -> Dict[str, Any]:
        return self.get_5min(symbol, start_date, end_date, adjust)

    def get_stock_5min(self, symbol: str, start_date: str = "", end_date: str = "", adjust: str = "forward") -> Dict[str, Any]:
        return self.get_5min(symbol, start_date, end_date, adjust)

    def _fetch_kline(
        self,
        symbol: str,
        period: str,
        endpoint_name: str,
        start_date: str,
        end_date: str,
        adjust: str,
    ) -> Dict[str, Any]:
        symbol = (symbol or "").strip()
        if not symbol:
            return {"code": 400, "data": None, "message": "symbol 不能为空"}

        def _call() -> Dict[str, Any]:
            if self._client is None:
                return {"code": 500, "data": None, "message": "TickFlow SDK 未初始化"}
            try:
                kwargs: Dict[str, Any] = {"period": period, "adjust": adjust}
                if start_date:
                    kwargs["start_time"] = self._date_to_ms(start_date, end_of_day=False)
                if end_date:
                    kwargs["end_time"] = self._date_to_ms(end_date, end_of_day=True)

                # 显式传 count=10000（SDK 上限）。当仅指定 start/end 时，SDK 默认 count=100，
                # 会导致日期范围内的早期数据被截断（例如 5m 周期下 100 根仅覆盖约 2 个交易日）。
                if start_date or end_date:
                    kwargs["count"] = 10000

                kline = self.client.klines.get(symbol, **kwargs)
                rows = self._kline_to_rows(kline, period=period)
                return {"code": 200, "data": rows}
            except Exception as exc:
                logger.error("TickFlow kline(%s %s) 失败: %s", symbol, period, exc)
                return {"code": 500, "data": None, "message": str(exc)}

        params = {
            "symbol": symbol,
            "period": period,
            "adjust": adjust,
            "start_date": start_date or "",
            "end_date": end_date or "",
        }
        return self._cached_call(endpoint_name, params, _call)

    @staticmethod
    def _date_to_ms(date_str: str, end_of_day: bool) -> int:
        """将 ``YYYY-MM-DD`` 转为毫秒时间戳（中国时区 / Asia/Shanghai）。"""
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if end_of_day:
            dt = dt.replace(hour=23, minute=59, second=59, microsecond=999000)
        # 视为中国时区，转为 UTC 后生成毫秒时间戳
        dt_cn = dt.replace(tzinfo=CN_TZ)
        return int(dt_cn.timestamp() * 1000)

    @staticmethod
    def _kline_to_rows(kline: Any, period: str) -> List[Dict[str, Any]]:
        """将 TickFlow 的列式 CompactKlineData 转换为行式 dict 列表。"""
        # SDK 在 as_dataframe=False 时返回 dict，含 timestamp/open/high/low/close/volume/amount 列表
        if not isinstance(kline, dict):
            return []
        timestamps = kline.get("timestamp") or []
        opens = kline.get("open") or []
        highs = kline.get("high") or []
        lows = kline.get("low") or []
        closes = kline.get("close") or []
        volumes = kline.get("volume") or []
        amounts = kline.get("amount") or []

        rows: List[Dict[str, Any]] = []
        for idx, ts_ms in enumerate(timestamps):
            try:
                # TickFlow 返回 UTC 毫秒时间戳；中国时区展示
                if period in ("1d", "1w", "1M"):
                    date_str = (
                        datetime.fromtimestamp(ts_ms / 1000, tz=CN_TZ)
                        .strftime("%Y-%m-%d")
                    )
                else:
                    date_str = (
                        datetime.fromtimestamp(ts_ms / 1000, tz=CN_TZ)
                        .strftime("%Y-%m-%d %H:%M:%S")
                    )
            except (OverflowError, OSError, ValueError, TypeError):
                continue

            def _at(arr, default=None):
                try:
                    return arr[idx] if idx < len(arr) else default
                except (IndexError, TypeError):
                    return default

            rows.append(
                {
                    "date": date_str,
                    "open": _at(opens),
                    "high": _at(highs),
                    "low": _at(lows),
                    "close": _at(closes),
                    "volume": _at(volumes),
                    "amount": _at(amounts),
                }
            )
        return rows

    # ------------------------------------------------------------------
    # 端点：代码搜索（本地缓存过滤）
    # ------------------------------------------------------------------

    def _fetch_instrument_names(self, symbols: List[str]) -> Dict[str, str]:
        """调用 ``client.instruments.batch`` 拉取名称，缓存为 ``instruments_meta`` 内存表。

        Args:
            symbols: 目标 symbol 列表（如 ``['510300.SH', '159915.SZ']``）

        Returns:
            ``{symbol: name}`` 映射；拉取失败时为空 dict。
        """
        if not symbols:
            return {}

        cached = self._instrument_name_cache
        # 区分「未缓存」与「已缓存但名称为空」
        missing = [s for s in symbols if s not in cached]
        if not missing:
            return {s: (cached.get(s) or "") for s in symbols}

        if self._client is None:
            return {s: (cached.get(s) or "") for s in symbols}

        try:
            # instruments.batch 一次最多 1000 个，按需分批
            for i in range(0, len(missing), 1000):
                batch = missing[i : i + 1000]
                details = self._client.instruments.batch(batch) or []
                for d in details:
                    sym = d.get("symbol", "")
                    name = (d.get("name") or "").strip()
                    if sym:
                        cached[sym] = name
            # 仍未命中的 symbol 标记为已尝试（空字符串），避免反复请求
            for s in missing:
                cached.setdefault(s, "")
            return {s: (cached.get(s) or "") for s in symbols}
        except Exception as exc:
            logger.warning("TickFlow instruments.batch 失败: %s", exc)
            return {s: (cached.get(s) or "") for s in symbols}

    def search_by_ticker(self, ticker: str, country_code: str = "CHN") -> Dict[str, Any]:
        """在已加载的 universe 中按 ticker 前缀 / 子串模糊匹配。

        返回结构与旧 Tsanghi 接口兼容：
        ``{'code': 200, 'data': [{'ticker', 'exchange_code', 'name', 'type', 'symbol', ...}, ...]}``

        ``name`` 字段通过 ``instruments.batch`` 按需补全（带内存级缓存）。
        """
        if not ticker:
            return {"code": 200, "data": []}

        query = str(ticker).strip()

        # 港美股直通路径：country 已明确判定为 HKG / USA 时，CN universe 必然不含
        # 该标的，直接按 country 构造记录并返回。
        # 不能先扫 CN universe：子串模糊匹配会让 0700（腾讯）误中 000700（模塑科技）。
        short = self._country_to_short(country_code)
        if short in ("HK", "US"):
            internal = "XHKG" if short == "HK" else "XNYS"
            if short == "HK":
                # 港股补零到 5 位（TickFlow 格式：00700.HK / 03032.HK）
                norm = str(int(query)).zfill(5) if query.isdigit() else query
            else:
                norm = query.upper()
            symbol = f"{norm}.{short}"
            sec_type = "ETF" if is_etf_ticker(norm, internal) else "STOCK"
            name_map = self._fetch_instrument_names([symbol])
            record = {
                "ticker": norm,
                "symbol": symbol,
                "exchange_code": internal,
                "name": name_map.get(symbol, ""),
                "type": sec_type,
            }
            logger.info(
                "search_by_ticker 港美股直通: country=%s ticker=%s → %s (%s)",
                country_code, query, symbol, sec_type,
            )
            return {"code": 200, "data": [record]}

        # 收集 universe 数据（按需触发 SDK 调用 + 文件缓存）
        items: List[Dict[str, Any]] = []
        for universe_id in self.DEFAULT_UNIVERSES:
            resp = self.get_universe(universe_id)
            if resp.get("code") == 200 and isinstance(resp.get("data"), dict):
                for sym in (resp["data"].get("symbols") or []):
                    items.append(
                        {
                            "symbol": sym,
                            "type": "ETF" if universe_id == "CN_ETF" else "STOCK",
                        }
                    )

        # 模糊匹配：ticker 与去掉后缀的纯代码做 startswith / 包含
        matches: List[Dict[str, Any]] = []
        seen_keys: set = set()
        matched_symbols: List[str] = []
        for item in items:
            symbol = item.get("symbol", "")
            raw_ticker = symbol.split(".", 1)[0] if "." in symbol else symbol
            if not (raw_ticker.startswith(query) or query in raw_ticker):
                continue
            # 同 universe 内同 symbol 去重；ETF 优先于 STOCK
            key = symbol
            if key in seen_keys:
                # 已有但当前是 ETF，则升级；否则跳过
                existing_idx = next(
                    (i for i, m in enumerate(matches) if m["symbol"] == key),
                    None,
                )
                if (
                    existing_idx is not None
                    and item.get("type") == "ETF"
                    and matches[existing_idx]["type"] != "ETF"
                ):
                    matches[existing_idx] = {
                        "ticker": raw_ticker,
                        "symbol": symbol,
                        "exchange_code": self._short_to_internal(
                            symbol.rsplit(".", 1)[-1] if "." in symbol else ""
                        ),
                        "name": "",
                        "type": "ETF",
                    }
                continue
            seen_keys.add(key)
            matched_symbols.append(symbol)
            matches.append(
                {
                    "ticker": raw_ticker,
                    "symbol": symbol,
                    "exchange_code": self._short_to_internal(
                        symbol.rsplit(".", 1)[-1] if "." in symbol else ""
                    ),
                    "name": "",
                    "type": item.get("type", "STOCK"),
                }
            )

        # 优先返回 startswith 命中，再按 ticker 长度升序
        matches.sort(key=lambda x: (not x["ticker"].startswith(query), len(x["ticker"]), x["ticker"]))

        # 限制前 N 条匹配后再拉名称，避免批量拉全量 universe
        top_symbols = [m["symbol"] for m in matches[:20]]
        name_map = self._fetch_instrument_names(top_symbols) if top_symbols else {}
        for m in matches[:20]:
            m["name"] = name_map.get(m["symbol"], "")

        return {"code": 200, "data": matches}

    @staticmethod
    def _short_to_internal(short: str) -> str:
        return {
            "SH": "XSHG", "SZ": "XSHE", "HK": "XHKG", "US": "XNYS"
        }.get(short.upper(), short.upper())

    @staticmethod
    def _country_to_short(country_code: str) -> str:
        """将业务层 country code（CHN/HKG/USA 等）映射为 exchange 短代码（SH/SZ/HK/US）。

        无法识别时返回空字符串，调用方据此决定是否触发 fallback。
        """
        if not country_code:
            return ""
        code = country_code.strip().upper()
        return {
            "CHN": "SH",  # CHN 默认按沪市处理（与项目当前聚焦 A 股的语境一致）
            "HKG": "HK",
            "USA": "US",
        }.get(code, "")

    # ------------------------------------------------------------------
    # 缓存管理（与 BaseProvider 兼容接口）
    # ------------------------------------------------------------------

    def clear_cache(self, endpoint_name: Optional[str] = None) -> None:
        if endpoint_name:
            self.cache_manager.clear(self.provider_name, endpoint_name)
        else:
            self.cache_manager.clear(self.provider_name)

    def get_cache_stats(self) -> Dict[str, Any]:
        return self.cache_manager.get_cache_stats()

    def cleanup_expired_cache(self) -> None:
        self.cache_manager.cleanup_expired()

    # ------------------------------------------------------------------
    # 关闭资源
    # ------------------------------------------------------------------

    def close(self) -> None:
        """显式关闭 SDK 客户端（如果有）。"""
        client = self._client
        if client is not None and hasattr(client, "close"):
            try:
                client.close()
            except Exception:  # pragma: no cover
                pass
        self._client = None

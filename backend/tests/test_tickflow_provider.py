"""``TickFlowProvider`` 单元测试。

覆盖：
- 静态辅助方法 ``_kline_to_rows`` / ``_normalize_quote`` / ``_date_to_ms``
- 离线日历 ``get_calendar``（基于 ``exchange_calendars`` 真实行为）
- 搜索 ``search_by_ticker`` 在 mock 后的 universe 数据上的过滤与排序
- 缓存 ``_cached_call`` 命中 / 未命中 / 失败分支
"""

import os
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

# 让 TickFlow() 无参构造时不会因缺少 key 抛错
os.environ.setdefault("TICKFLOW_API_KEY", "test_placeholder_key")

# 中国时区，与 provider 内部保持一致
CN_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")

from app.external.providers.tickflow_provider import (  # noqa: E402
    TickFlowProvider,
    _coerce_params,
)


# ---------------------------------------------------------------------------
# 纯函数
# ---------------------------------------------------------------------------


def test_coerce_params_simple():
    out = _coerce_params({"a": 1, "b": "x", "c": None, "d": True})
    assert out == {"a": 1, "b": "x", "c": None, "d": True}


def test_coerce_params_serializes_complex_values():
    out = _coerce_params({"list": [1, 2, 3], "obj": {"k": "v"}})
    assert out["list"] == "[1, 2, 3]"
    assert out["obj"] == '{"k": "v"}'


def test_coerce_params_none():
    assert _coerce_params(None) == {}
    assert _coerce_params({}) == {}


def test_provider_initialize_with_placeholder_key():
    """初始化：缺 API Key 时也能成功构造（仅警告）。"""
    with patch.dict(os.environ, {"TICKFLOW_API_KEY": ""}, clear=False):
        provider = TickFlowProvider()
        # SDK 仍然成功初始化（占位 key），不会因缺失导致异常
        assert provider is not None


def test_short_to_internal():
    assert TickFlowProvider._short_to_internal("SH") == "XSHG"
    assert TickFlowProvider._short_to_internal("SZ") == "XSHE"
    assert TickFlowProvider._short_to_internal("HK") == "XHKG"
    assert TickFlowProvider._short_to_internal("US") == "XNYS"
    assert TickFlowProvider._short_to_internal("XX") == "XX"  # 未知值原样返回


def test_date_to_ms_start_and_end_of_day():
    start_ms = TickFlowProvider._date_to_ms("2025-01-10", end_of_day=False)
    end_ms = TickFlowProvider._date_to_ms("2025-01-10", end_of_day=True)
    assert end_ms > start_ms
    # 一整天 86400000 ms ± 1 秒
    assert (end_ms - start_ms) >= 86_400_000 - 1000
    assert (end_ms - start_ms) <= 86_400_000 + 1000


def test_kline_to_rows_columnar_to_row():
    """``_kline_to_rows`` 把 SDK 列式结构转行式 dict 列表。"""
    # 时间戳表示 2025-01-10 00:00 / 2025-01-11 00:00 中国时区
    columnar = {
        "timestamp": [
            int(datetime(2025, 1, 10, 0, 0, 0, tzinfo=CN_TZ).timestamp() * 1000),
            int(datetime(2025, 1, 11, 0, 0, 0, tzinfo=CN_TZ).timestamp() * 1000),
        ],
        "open": [3.5, 3.6],
        "high": [3.55, 3.65],
        "low": [3.45, 3.55],
        "close": [3.50, 3.62],
        "volume": [1000, 1500],
        "amount": [3500.0, 5400.0],
    }
    rows = TickFlowProvider._kline_to_rows(columnar, period="1d")
    assert len(rows) == 2
    assert rows[0]["date"] == "2025-01-10"
    assert rows[0]["open"] == 3.5
    assert rows[1]["close"] == 3.62


def test_kline_to_rows_intraday_format():
    """非日线 K 线应保留 ``YYYY-MM-DD HH:MM:SS`` 格式。"""
    ts = int(datetime(2025, 1, 10, 9, 35, 0, tzinfo=CN_TZ).timestamp() * 1000)
    columnar = {
        "timestamp": [ts],
        "open": [1.0],
        "high": [1.0],
        "low": [1.0],
        "close": [1.0],
        "volume": [1],
        "amount": [1.0],
    }
    rows = TickFlowProvider._kline_to_rows(columnar, period="5m")
    assert rows[0]["date"] == "2025-01-10 09:35:00"


def test_kline_to_rows_invalid_input():
    assert TickFlowProvider._kline_to_rows(None, period="1d") == []
    assert TickFlowProvider._kline_to_rows("not a dict", period="1d") == []


def test_normalize_quote_a_share():
    """``_normalize_quote`` 提取 ticker/exchange_code 并计算 change_pct。"""
    quote = {
        "symbol": "510300.SH",
        "name": "沪深300ETF",
        "last_price": 3.6,
        "prev_close": 3.5,
        "open": 3.5,
        "high": 3.65,
        "low": 3.48,
        "volume": 10000,
        "amount": 35000.0,
        # 2025-01-10 15:00:00 中国时区
        "timestamp": int(datetime(2025, 1, 10, 15, 0, 0, tzinfo=CN_TZ).timestamp() * 1000),
    }
    out = TickFlowProvider._normalize_quote(quote)
    assert out["symbol"] == "510300.SH"
    assert out["ticker"] == "510300"
    assert out["exchange_code"] == "XSHG"
    assert out["close"] == 3.6
    assert out["pre_close"] == 3.5
    assert out["date"] == "2025-01-10 15:00:00"
    # change_pct = (3.6 - 3.5) / 3.5 * 100 ≈ 2.857
    assert out["change_pct"] == pytest.approx(2.857, rel=1e-2)


def test_normalize_quote_hk_and_us():
    hk = TickFlowProvider._normalize_quote({"symbol": "00700.HK", "last_price": 100, "prev_close": 99})
    assert hk["exchange_code"] == "XHKG"
    us = TickFlowProvider._normalize_quote({"symbol": "AAPL.US", "last_price": 200, "prev_close": 195})
    assert us["exchange_code"] == "XNYS"


def test_normalize_quote_change_pct_zero_prev():
    """prev_close 为 0 时 change_pct 应为 None，不抛异常。"""
    out = TickFlowProvider._normalize_quote({"symbol": "510300.SH", "last_price": 1.0, "prev_close": 0})
    assert out["change_pct"] is None


def test_normalize_quote_missing_timestamp():
    """timestamp 缺失时 date 留空字符串。"""
    out = TickFlowProvider._normalize_quote({"symbol": "510300.SH", "last_price": 1.0, "prev_close": 1.0})
    assert out["date"] == ""


# ---------------------------------------------------------------------------
# exchange_calendars 集成
# ---------------------------------------------------------------------------


def test_get_calendar_xshg_returns_descending_dates():
    """get_calendar(XSHG) 应返回降序日期字符串列表。"""
    provider = TickFlowProvider()
    resp = provider.get_calendar("XSHG", limit=5)
    assert resp["code"] == 200
    dates = [row["date"] for row in resp["data"]]
    assert len(dates) >= 1
    # 降序
    assert dates == sorted(dates, reverse=True)
    # 至少第一条是工作日
    assert all(d.count("-") == 2 for d in dates)


def test_get_calendar_respects_date_range():
    provider = TickFlowProvider()
    resp = provider.get_calendar("XSHG", start_date="2025-01-06", end_date="2025-01-10")
    assert resp["code"] == 200
    dates = [row["date"] for row in resp["data"]]
    # 2025-01-06 ~ 2025-01-10 中只有 01-06、01-07、01-08、01-09、01-10 是工作日
    assert "2025-01-06" in dates
    assert "2025-01-10" in dates
    # 周末 01-11、01-12 不应出现
    assert "2025-01-11" not in dates
    assert "2025-01-12" not in dates


def test_get_calendar_unknown_exchange():
    provider = TickFlowProvider()
    resp = provider.get_calendar("FAKE", limit=5)
    assert resp["code"] == 400
    assert "不支持" in resp.get("message", "")


# ---------------------------------------------------------------------------
# _fetch_kline count 参数
# ---------------------------------------------------------------------------


def test_fetch_kline_passes_count_when_date_range_given(tmp_path):
    """指定 start_date/end_date 时必须显式传 count=10000（SDK 上限），否则默认 100 根
    会导致日期范围早期的数据被截断（5m 周期下 100 根仅 ~2 个交易日）。"""
    from unittest.mock import MagicMock
    provider = TickFlowProvider()
    # 隔离缓存目录，避免与生产缓存冲突
    provider.cache_manager.cache_dir = tmp_path / "cache"
    provider.cache_manager.cache_dir.mkdir(parents=True, exist_ok=True)
    fake_klines = MagicMock()
    fake_klines.get = MagicMock(
        return_value={"timestamp": [], "open": [], "high": [], "low": [], "close": [], "volume": [], "amount": []}
    )
    fake_client = MagicMock()
    fake_client.klines = fake_klines
    provider._client = fake_client

    provider._fetch_kline("510300.SH", "5m", "kline_5min", "2025-04-24", "2025-06-09", "forward")

    fake_klines.get.assert_called_once()
    _, kwargs = fake_klines.get.call_args
    assert kwargs.get("count") == 10000, "日期范围请求必须显式传 count=10000"
    assert kwargs.get("start_time") is not None
    assert kwargs.get("end_time") is not None


def test_fetch_kline_no_count_when_no_date_range(tmp_path):
    """未指定日期范围时不强行传 count，由 SDK 默认行为决定（适合临时查询最新 N 根）。"""
    from unittest.mock import MagicMock
    provider = TickFlowProvider()
    provider.cache_manager.cache_dir = tmp_path / "cache"
    provider.cache_manager.cache_dir.mkdir(parents=True, exist_ok=True)
    fake_klines = MagicMock()
    fake_klines.get = MagicMock(
        return_value={"timestamp": [], "open": [], "high": [], "low": [], "close": [], "volume": [], "amount": []}
    )
    fake_client = MagicMock()
    fake_client.klines = fake_klines
    provider._client = fake_client

    provider._fetch_kline("510300.SH", "1d", "daily", "", "", "forward")

    fake_klines.get.assert_called_once()
    _, kwargs = fake_klines.get.call_args
    assert "count" not in kwargs, "未指定日期时不应强行传 count"


# ---------------------------------------------------------------------------
# search_by_ticker（mock universe 响应）
# ---------------------------------------------------------------------------


def _universe_resp(symbols, universe_id):
    return {
        "code": 200,
        "data": {
            "id": universe_id,
            "name": universe_id,
            "category": "etf" if "ETF" in universe_id else "equity",
            "symbols": symbols,
        },
    }


def test_search_by_ticker_startswith_priority():
    provider = TickFlowProvider()
    with patch.object(
        provider,
        "get_universe",
        side_effect=[
            _universe_resp(["510300.SH", "510500.SH", "159915.SZ"], "CN_ETF"),
            # 510300 同时出现在 A 股，但 ETF 类型会覆盖 STOCK
            _universe_resp(["510300.SH", "600000.SH", "000001.SZ"], "CN_Equity_A"),
        ],
    ), patch.object(
        provider, "_fetch_instrument_names", return_value={"510300.SH": "沪深300ETF", "510500.SH": "中证500ETF"}
    ):
        resp = provider.search_by_ticker("510", "CHN")
    assert resp["code"] == 200
    tickers = [item["ticker"] for item in resp["data"]]
    # 去重后：以 510 开头的应有 2 条（510300 / 510500）
    starts_with = [t for t in tickers if t.startswith("510")]
    assert len(starts_with) == 2
    # 510300 的类型应被 ETF 覆盖
    by_ticker = {item["ticker"]: item for item in resp["data"]}
    assert by_ticker["510300"]["type"] == "ETF"
    # 名称字段被 instruments.batch 补全
    assert by_ticker["510300"]["name"] == "沪深300ETF"
    assert by_ticker["510500"]["name"] == "中证500ETF"
    # 短 ticker（510500, 510300 都是 6 位）字典序应一致
    assert tickers[0] in ("510300", "510500")


def test_search_by_ticker_returns_typed_result():
    provider = TickFlowProvider()
    with patch.object(
        provider,
        "get_universe",
        side_effect=[
            _universe_resp(["510300.SH"], "CN_ETF"),
            _universe_resp([], "CN_Equity_A"),
        ],
    ), patch.object(
        provider, "_fetch_instrument_names", return_value={"510300.SH": "沪深300ETF"}
    ):
        resp = provider.search_by_ticker("510300", "CHN")
    assert resp["code"] == 200
    assert resp["data"][0]["type"] == "ETF"
    assert resp["data"][0]["exchange_code"] == "XSHG"
    assert resp["data"][0]["symbol"] == "510300.SH"
    assert resp["data"][0]["name"] == "沪深300ETF"


def test_search_by_ticker_empty_input():
    provider = TickFlowProvider()
    resp = provider.search_by_ticker("", "CHN")
    assert resp["code"] == 200
    assert resp["data"] == []


# ---------------------------------------------------------------------------
# 港美股直通路径（country=HKG/USA 时跳过 CN universe，直接构造记录）
# ---------------------------------------------------------------------------


def test_search_by_ticker_hk_direct_etf():
    """HKG + ETF 白名单代码 → 直通返回 XHKG ETF 记录（5 位补零），不触碰 universe。"""
    provider = TickFlowProvider()
    with patch.object(provider, "get_universe") as mock_uni, patch.object(
        provider, "_fetch_instrument_names", return_value={"03032.HK": "恒生科技ETF"}
    ):
        resp = provider.search_by_ticker("3032", "HKG")
    mock_uni.assert_not_called()  # 港股直通，不扫 CN universe
    assert resp["code"] == 200
    assert len(resp["data"]) == 1
    item = resp["data"][0]
    assert item["ticker"] == "03032"
    assert item["symbol"] == "03032.HK"
    assert item["exchange_code"] == "XHKG"
    assert item["type"] == "ETF"  # 3032 在 _KNOWN_HK_ETFS 白名单中
    assert item["name"] == "恒生科技ETF"


def test_search_by_ticker_hk_direct_stock():
    """HKG + 非白名单代码（0700 腾讯）→ 直通返回 STOCK 记录。"""
    provider = TickFlowProvider()
    with patch.object(provider, "get_universe") as mock_uni, patch.object(
        provider, "_fetch_instrument_names", return_value={"00700.HK": "腾讯控股"}
    ):
        resp = provider.search_by_ticker("0700", "HKG")
    mock_uni.assert_not_called()
    assert resp["code"] == 200
    assert len(resp["data"]) == 1
    item = resp["data"][0]
    assert item["symbol"] == "00700.HK"
    assert item["exchange_code"] == "XHKG"
    assert item["type"] == "STOCK"  # 0700 是腾讯股票，不在 ETF 白名单
    assert item["name"] == "腾讯控股"


def test_search_by_ticker_hk_not_polluted_by_cn_universe():
    """回归：0700 (HKG) 不得被 CN universe 的 000700 子串误中。"""
    provider = TickFlowProvider()
    with patch.object(
        provider,
        "get_universe",
        side_effect=lambda uid: _universe_resp(
            ["000700.SZ"] if uid == "CN_Equity_A" else [], uid
        ),
    ) as mock_uni, patch.object(provider, "_fetch_instrument_names", return_value={}):
        resp = provider.search_by_ticker("0700", "HKG")
    mock_uni.assert_not_called()  # 直通路径下根本不应触发 universe 扫描
    assert resp["code"] == 200
    assert len(resp["data"]) == 1
    assert resp["data"][0]["symbol"] == "00700.HK"  # 而不是 000700.SZ
    assert resp["data"][0]["exchange_code"] == "XHKG"


def test_search_by_ticker_us_direct_etf():
    """USA + ETF 白名单代码（SPY）→ 直通返回 XNYS ETF 记录。"""
    provider = TickFlowProvider()
    with patch.object(provider, "get_universe") as mock_uni, patch.object(
        provider, "_fetch_instrument_names", return_value={"SPY.US": "SPDR S&P 500"}
    ):
        resp = provider.search_by_ticker("spy", "USA")
    mock_uni.assert_not_called()
    assert resp["code"] == 200
    assert len(resp["data"]) == 1
    item = resp["data"][0]
    assert item["ticker"] == "SPY"  # 小写输入被规范化为大写
    assert item["symbol"] == "SPY.US"
    assert item["exchange_code"] == "XNYS"
    assert item["type"] == "ETF"  # SPY 在 _KNOWN_US_ETFS 白名单中
    assert item["name"] == "SPDR S&P 500"


def test_search_by_ticker_us_direct_stock():
    """USA + 非白名单代码（AAPL 苹果）→ 直通返回 STOCK 记录。"""
    provider = TickFlowProvider()
    with patch.object(provider, "get_universe") as mock_uni, patch.object(
        provider, "_fetch_instrument_names", return_value={}
    ):
        resp = provider.search_by_ticker("AAPL", "USA")
    mock_uni.assert_not_called()
    assert resp["code"] == 200
    assert len(resp["data"]) == 1
    item = resp["data"][0]
    assert item["symbol"] == "AAPL.US"
    assert item["type"] == "STOCK"


def test_search_by_ticker_fallback_chn_not_triggered():
    """CHN 走 CN universe，universe 全空时不应触发任何直通 / fallback（HKG/US 限定）。"""
    provider = TickFlowProvider()
    with patch.object(
        provider,
        "get_universe",
        side_effect=[
            _universe_resp([], "CN_ETF"),
            _universe_resp([], "CN_Equity_A"),
        ],
    ), patch.object(provider, "_fetch_instrument_names", return_value={}):
        resp = provider.search_by_ticker("510300", "CHN")
    assert resp["code"] == 200
    assert resp["data"] == []


def test_country_to_short_mapping():
    assert TickFlowProvider._country_to_short("CHN") == "SH"
    assert TickFlowProvider._country_to_short("HKG") == "HK"
    assert TickFlowProvider._country_to_short("USA") == "US"
    assert TickFlowProvider._country_to_short("chn") == "SH"  # 大小写不敏感
    assert TickFlowProvider._country_to_short("XXX") == ""  # 未知值返回空串
    assert TickFlowProvider._country_to_short("") == ""


def test_fetch_instrument_names_uses_sdk_and_caches():
    """_fetch_instrument_names：未命中的 symbol 调用 instruments.batch 并写入缓存。"""
    provider = TickFlowProvider()
    provider._client = MagicMock()
    provider._client.instruments.batch = MagicMock(
        return_value=[{"symbol": "510300.SH", "name": "沪深300ETF"}]
    )

    # 第一次：未命中，调用 SDK
    out1 = provider._fetch_instrument_names(["510300.SH", "159915.SZ"])
    assert out1 == {"510300.SH": "沪深300ETF", "159915.SZ": ""}
    assert provider._instrument_name_cache["510300.SH"] == "沪深300ETF"
    assert provider._instrument_name_cache["159915.SZ"] == ""  # 标记已尝试
    assert provider._client.instruments.batch.call_count == 1

    # 第二次：缓存命中，不调用 SDK
    provider._client.instruments.batch.reset_mock()
    out2 = provider._fetch_instrument_names(["510300.SH", "159915.SZ"])
    assert out2 == {"510300.SH": "沪深300ETF", "159915.SZ": ""}
    assert provider._client.instruments.batch.call_count == 0


def test_fetch_instrument_names_batches_large_input():
    """超过 1000 个 symbol 时按 1000 切分。"""
    provider = TickFlowProvider()
    provider._client = MagicMock()
    provider._client.instruments.batch = MagicMock(return_value=[])

    # 构造 1500 个 symbol
    symbols = [f"60000{i:03d}.SH" for i in range(1500)]
    provider._fetch_instrument_names(symbols)

    # 期望被切为 1000 + 500 两次
    assert provider._client.instruments.batch.call_count == 2
    first_call, second_call = provider._client.instruments.batch.call_args_list
    assert len(first_call.args[0]) == 1000
    assert len(second_call.args[0]) == 500


def test_fetch_instrument_names_handles_sdk_failure():
    """SDK 抛异常时返回缓存中的已有值（缺失项为空字符串），不向上抛。"""
    provider = TickFlowProvider()
    provider._client = MagicMock()
    provider._client.instruments.batch = MagicMock(side_effect=Exception("network down"))
    provider._instrument_name_cache["510300.SH"] = "cached-name"

    out = provider._fetch_instrument_names(["510300.SH", "159915.SZ"])
    assert out["510300.SH"] == "cached-name"
    assert out["159915.SZ"] == ""


# ---------------------------------------------------------------------------
# 缓存流程
# ---------------------------------------------------------------------------


def test_cached_call_hit_and_miss(tmp_path, monkeypatch):
    """_cached_call 第一次未命中会调用 producer；第二次缓存命中跳过 producer。"""
    # 切换缓存目录到临时目录
    monkeypatch.setenv("TICKFLOW_API_KEY", "test")
    cfg_path = "app/config/config.yaml"
    provider = TickFlowProvider()
    # 重定向 cache_dir
    provider.cache_manager.cache_dir = tmp_path / "cache"
    provider.cache_manager.cache_dir.mkdir(parents=True, exist_ok=True)

    producer = MagicMock(return_value={"code": 200, "data": [{"x": 1}]})
    params = {"symbol": "510300.SH"}

    # 第一次：缓存未命中，调用 producer
    out1 = provider._cached_call("realtime", params, producer)
    producer.assert_called_once()
    assert out1 == {"code": 200, "data": [{"x": 1}]}

    # 第二次：缓存命中，不再调用 producer
    producer.reset_mock()
    out2 = provider._cached_call("realtime", params, producer)
    producer.assert_not_called()
    assert out2 == {"code": 200, "data": [{"x": 1}]}


def test_cached_call_does_not_cache_error(monkeypatch):
    """失败响应不应被缓存。"""
    monkeypatch.setenv("TICKFLOW_API_KEY", "test")
    provider = TickFlowProvider()
    provider.cache_manager.cache_dir = __import__("pathlib").Path("cache/_test_temp")
    provider.cache_manager.cache_dir.mkdir(parents=True, exist_ok=True)

    failing = MagicMock(return_value={"code": 500, "data": None, "message": "boom"})
    out = provider._cached_call("realtime", {"symbol": "FAIL.SH"}, failing)
    assert out["code"] == 500

    # 再次调用应重新触发 producer（因为失败不缓存）
    failing.reset_mock()
    provider._cached_call("realtime", {"symbol": "FAIL.SH"}, failing)
    assert failing.call_count == 1

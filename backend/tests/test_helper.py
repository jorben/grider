"""``app.utils.helper`` 单元测试。

覆盖：
- ``normalize_exchange_code`` 对多种别名的归一化
- ``ticker_to_tickflow`` / ``tickflow_to_ticker`` 双向转换
- ``is_etf_ticker`` / ``detect_security_type`` 的判定规则
- ``determine_country`` 旧接口的回归
"""

import pytest

from app.utils.helper import (
    detect_security_type,
    determine_country,
    is_etf_ticker,
    normalize_exchange_code,
    ticker_to_tickflow,
    tickflow_to_ticker,
)


# ---------------------------------------------------------------------------
# normalize_exchange_code
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("XSHG", "SH"),
        ("XSHE", "SZ"),
        ("XHKG", "HK"),
        ("XNYS", "US"),
        ("SH", "SH"),
        ("SZ", "SZ"),
        ("SSE", "SH"),
        ("SZSE", "SZ"),
        ("HKEX", "HK"),
        ("NASDAQ", "US"),
        ("USA", "US"),
        ("sh", "SH"),
        ("  XSHG  ", "SH"),
    ],
)
def test_normalize_exchange_code_aliases(raw, expected):
    assert normalize_exchange_code(raw) == expected


def test_normalize_exchange_code_unknown():
    # 未识别的代码原样返回大写
    assert normalize_exchange_code("unknown") == "UNKNOWN"


def test_normalize_exchange_code_empty():
    assert normalize_exchange_code("") == ""
    assert normalize_exchange_code(None) == ""


# ---------------------------------------------------------------------------
# ticker_to_tickflow / tickflow_to_ticker
# ---------------------------------------------------------------------------


def test_ticker_to_tickflow_a_share():
    assert ticker_to_tickflow("510300", "XSHG") == "510300.SH"
    assert ticker_to_tickflow("510300", "SSE") == "510300.SH"
    assert ticker_to_tickflow("510300", "SH") == "510300.SH"
    assert ticker_to_tickflow("000001", "XSHE") == "000001.SZ"
    assert ticker_to_tickflow("000001", "SZSE") == "000001.SZ"


def test_ticker_to_tickflow_preserves_leading_zeros():
    # A 股 6 位前导零必须保留
    assert ticker_to_tickflow("600000", "XSHG") == "600000.SH"
    assert ticker_to_tickflow("600000", "SSE") == "600000.SH"
    assert ticker_to_tickflow("300750", "SZSE") == "300750.SZ"


def test_ticker_to_tickflow_hk_pads_to_four():
    # 港股 < 6 位补零到 4 位
    assert ticker_to_tickflow("700", "XHKG") == "0700.HK"
    assert ticker_to_tickflow("700", "HK") == "0700.HK"


def test_ticker_to_tickflow_already_formatted():
    # 已带分隔符直接规范化
    assert ticker_to_tickflow("510300.SS", "XSHG") == "510300.SH"
    assert ticker_to_tickflow("aapl.us", "") == "AAPL.US"


def test_ticker_to_tickflow_us_fallback():
    # 非数字 ticker 默认 US 后缀
    assert ticker_to_tickflow("AAPL", "USA") == "AAPL.US"
    assert ticker_to_tickflow("AAPL", "") == "AAPL.US"


def test_ticker_to_tickflow_empty():
    assert ticker_to_tickflow("", "XSHG") == ".SH"
    assert ticker_to_tickflow(None, "XSHG") == ".SH"


def test_tickflow_to_ticker_basic():
    assert tickflow_to_ticker("510300.SH") == ("510300", "XSHG")
    assert tickflow_to_ticker("000001.SZ") == ("000001", "XSHE")
    assert tickflow_to_ticker("00700.HK") == ("00700", "XHKG")
    assert tickflow_to_ticker("AAPL.US") == ("AAPL", "XNYS")


def test_tickflow_to_ticker_no_separator():
    assert tickflow_to_ticker("510300") == ("510300", "")


def test_tickflow_to_ticker_empty():
    assert tickflow_to_ticker("") == ("", "")
    assert tickflow_to_ticker(None) == ("", "")


def test_round_trip_a_share():
    sym = ticker_to_tickflow("510300", "XSHG")
    assert tickflow_to_ticker(sym) == ("510300", "XSHG")


def test_round_trip_hk():
    sym = ticker_to_tickflow("700", "XHKG")
    assert tickflow_to_ticker(sym) == ("0700", "XHKG")


# ---------------------------------------------------------------------------
# is_etf_ticker / detect_security_type
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ticker,exchange,expected",
    [
        ("510300", "XSHG", True),  # 5 开头 SH
        ("510500", "SH", True),
        ("512880", "SSE", True),
        ("588000", "XSHG", True),  # 科创 50ETF
        ("159915", "XSHE", True),  # 159 开头 SZ
        ("159919", "SZSE", True),
        ("000001", "XSHE", False),  # 普通深市股票
        ("600000", "XSHG", False),  # 普通沪市股票
        ("300750", "SZSE", False),  # 创业板
        ("00700", "XHKG", False),  # 港股非 ETF
    ],
)
def test_is_etf_ticker(ticker, exchange, expected):
    assert is_etf_ticker(ticker, exchange) is expected


def test_is_etf_ticker_non_digit():
    assert is_etf_ticker("AAPL", "XNYS") is False


def test_is_etf_ticker_short_code():
    # 不足 6 位视为非 ETF
    assert is_etf_ticker("510", "XSHG") is False


def test_is_etf_ticker_empty():
    assert is_etf_ticker("", "XSHG") is False
    assert is_etf_ticker(None, "XSHG") is False


def test_detect_security_type():
    assert detect_security_type("510300", "XSHG") == "ETF"
    assert detect_security_type("000001", "XSHE") == "STOCK"
    assert detect_security_type("AAPL", "XNYS") == "STOCK"


# ---------------------------------------------------------------------------
# determine_country（保留旧行为）
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "code,expected_ticker,expected_country",
    [
        ("510300", "510300", "CHN"),
        ("510500", "510500", "CHN"),
        ("600000", "600000", "CHN"),
        ("700", "0700", "HKG"),  # < 6 位补 0
        ("AAPL", "AAPL", "USA"),
        ("", "", "USA"),
        (None, "", "USA"),
    ],
)
def test_determine_country(code, expected_ticker, expected_country):
    assert determine_country(code) == (expected_ticker, expected_country)

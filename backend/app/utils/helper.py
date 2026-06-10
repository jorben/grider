"""通用辅助函数。

包含：
- 标的代码与国家/地区识别（determine_country，保留）
- 标的代码与 TickFlow 符号格式的双向转换（ticker_to_tickflow / tickflow_to_ticker）
- 不同交易所代码格式（XSHG/XSHE、SSE/SZSE、SH/SZ 等）的归一化与映射
- ETF 标的识别（is_etf_ticker）
- 交易所有效性校验

TickFlow 符号格式约定（见 docs/tsanghi_vs_tickflow_analysis.md 第 3.3 节）：
- A 股上交所：600000.SH
- A 股深交所：000001.SZ
- 港股      ：00700.HK
- 美股      ：AAPL.US
- ETF 同 A 股规则：510300.SH / 159915.SZ
"""

from __future__ import annotations

from typing import Optional, Tuple


# ---------------------------------------------------------------------------
# 交易所代码映射
# ---------------------------------------------------------------------------

# Tsanghi 旧格式 / 内部统一格式（XSHG/XSHE/XHKG/XNYS）
_INTERNAL_EXCHANGE_CODES = {"XSHG", "XSHE", "XHKG", "XNYS"}

# 标准化后的 TickFlow 短代码（SH/SZ/HK/US）
_TICKFLOW_EXCHANGE_CODES = {"SH", "SZ", "HK", "US"}

# 已知的交易所代码同义词（含行业常见写法与单字母别名）
# 全部归一化为 TickFlow 短代码（SH/SZ/HK/US）
_EXCHANGE_ALIAS_MAP = {
    # 上海证券交易所
    "XSHG": "SH", "SH": "SH", "SSE": "SH", "SS": "SH", "SHA": "SH",
    # 深圳证券交易所
    "XSHE": "SZ", "SZ": "SZ", "SZSE": "SZ", "ZS": "SZ", "SZA": "SZ",
    # 香港交易所
    "XHKG": "HK", "HK": "HK", "HKEX": "HK", "HKG": "HK",
    # 纽约证券交易所 / 纳斯达克（统一映射为 US）
    "XNYS": "US", "US": "US", "NYSE": "US", "NASDAQ": "US", "USA": "US",
}


def normalize_exchange_code(exchange_code: Optional[str]) -> str:
    """将各种交易所代码归一化为 TickFlow 短代码（SH/SZ/HK/US）。

    无法识别的输入会原样返回（大写），调用方应自行决定如何处理。
    """
    if not exchange_code:
        return ""
    code = str(exchange_code).strip().upper()
    return _EXCHANGE_ALIAS_MAP.get(code, code)


def _determine_country_from_ticker(ticker: str) -> str:
    """根据 ticker 字面值推断所属国家/地区（返回 TickFlow 短代码）。"""
    if not ticker:
        return ""
    if ticker.isdigit():
        if len(ticker) == 6:
            return "SH"  # 默认为沪市（与项目当前聚焦 A 股的语境一致）
        if len(ticker) < 6:
            return "HK"
    return "US"


def determine_country(code: str) -> Tuple[str, str]:
    """保留的旧接口：根据代码判断所属国家/地区（数字 / 港股 / 美股）。

    - 6 位数字 → ("ticker", "CHN")
    - <6 位数字 → 补零到 4 位，标记为 HKG
    - 非数字 → 原样返回，标记为 USA

    Args:
        code: 原始输入代码

    Returns:
        (处理后的 ticker, 国家代码)
    """
    if code is None:
        return "", "USA"
    code_str = str(code).strip()
    if not code_str:
        return "", "USA"
    if code_str.isdigit():
        if len(code_str) == 6:
            return code_str, "CHN"
        if len(code_str) < 6:
            processed = str(int(code_str)).zfill(4)
            return processed, "HKG"
    return code_str, "USA"


# ---------------------------------------------------------------------------
# 代码格式转换
# ---------------------------------------------------------------------------

# 已包含分隔符的 TickFlow 符号（形如 510300.SH / 00700.HK）
def ticker_to_tickflow(ticker: str, exchange_code: str) -> str:
    """将 ``(ticker, exchange_code)`` 转换为 TickFlow 符号 ``510300.SH``。

    规则：
    - 如果 ticker 已经带 ``.SH/.SZ/.HK/.US`` 后缀，直接规范化（去除前导零）后返回。
    - 否则根据 exchange_code 的别名映射补全后缀。
    - 6 位 A 股代码：保留前导零（如 600000 不变成 6）。
    - 港股 <6 位数字：补零到 4 位（沿用旧 determine_country 行为）。

    Args:
        ticker: 纯数字或字母数字代码
        exchange_code: 任意已知的交易所代码（XSHG/SSE/SH/XSHE/...）

    Returns:
        TickFlow 风格符号，例如 "510300.SH"、"00700.HK"、"AAPL.US"
    """
    if not ticker:
        ticker = ""
    ticker = str(ticker).strip()

    # 已带分隔符的情况
    if "." in ticker:
        prefix, _, suffix = ticker.rpartition(".")
        prefix = prefix.strip().upper()
        suffix = normalize_exchange_code(suffix) or suffix.upper()
        return f"{prefix}.{suffix}"

    ticker_upper = ticker.upper()
    exchange_short = normalize_exchange_code(exchange_code)

    # 数字 ticker（A 股 / 港股）
    if ticker.isdigit():
        if exchange_short == "HK" or (not exchange_short and len(ticker) < 6):
            # 港股补零到 5 位（TickFlow 格式：00700.HK / 03032.HK）
            padded = str(int(ticker)).zfill(5) if ticker else ""
            return f"{padded}.{exchange_short or 'HK'}"
        if exchange_short in ("SH", "SZ"):
            # A 股 6 位保留前导零
            padded = ticker.zfill(6)
            return f"{padded}.{exchange_short}"
        if exchange_short in _INTERNAL_EXCHANGE_CODES or exchange_short in _TICKFLOW_EXCHANGE_CODES:
            return f"{ticker.zfill(6)}.{exchange_short}"
        # 兜底：补零到 6 位 + US
        return f"{ticker.zfill(6)}.US"

    # 非数字 ticker（美股等）
    suffix = exchange_short or _determine_country_from_ticker(ticker)
    if not suffix:
        suffix = "US"
    return f"{ticker_upper}.{suffix}"


def tickflow_to_ticker(symbol: str) -> Tuple[str, str]:
    """将 TickFlow 符号（``510300.SH``）拆分为 ``(ticker, exchange_code)``。

    返回的 ``exchange_code`` 优先使用内部统一格式（XSHG/XSHE/XHKG/XNYS），
    保持与旧 Tsanghi 时代业务代码（``ETFAnalysisService`` 等）的兼容性。
    未携带分隔符的输入将原样返回并附空 exchange_code。
    """
    if not symbol:
        return "", ""
    symbol = str(symbol).strip()
    if "." not in symbol:
        return symbol, ""
    ticker, _, suffix = symbol.rpartition(".")
    short = normalize_exchange_code(suffix)
    internal = {
        "SH": "XSHG",
        "SZ": "XSHE",
        "HK": "XHKG",
        "US": "XNYS",
    }.get(short, short)
    return ticker, internal


# ---------------------------------------------------------------------------
# ETF 识别
# ---------------------------------------------------------------------------

# 经验性规则：
# - 上海 ETF：5xxxxx（沪深 300ETF、科创 50ETF 等）
# - 深圳 ETF：1xxxxx（159xxx 创业板 / 行业 ETF 居多）
# - 货币 / 债券 ETF：511 / 519 开头也属上海
# 完整 A 股 6 位代码以 5 开头 → 偏 ETF；159xxx 明确为深圳 ETF
_ETF_SHANGHAI_PREFIXES = ("5",)
_ETF_SHENZHEN_PREFIXES = ("1", "159")

# 港美股常见 ETF 集合（按代码字面量匹配；不含交易所后缀）。
# 用 whitelist 而非纯启发式的原因：港股 3-5 位、美股纯字母既包含 ETF 也包含个股，
# 纯形态启发式会把 0700（腾讯）、AAPL（苹果）等个股误判为 ETF。Whitelist 是更
# 保守的方案，仅放行业务方确认过的常见 ETF 代码。
_KNOWN_HK_ETFS = frozenset({
    "3032",   # 恒生科技 ETF
    "3033",   # 恒生科技 ETF（南方）
    "2823",   # 安硕 A50
    "2800",   # 盈富基金
    "7200",   # 南方两倍做多恒生科技
    "7560",   # 恒生科技 ETF
    "3174",   # 南方两倍做空恒生科技
    "9071",   # 中金恒生科技 ETF
})
_KNOWN_US_ETFS = frozenset({
    "SPY",   # 标普 500 ETF
    "QQQ",   # 纳斯达克 100 ETF
    "VOO",   #  Vanguard 标普 500 ETF
    "VTI",   #  Vanguard Total Stock Market
    "IVV",   # iShares Core S&P 500
    "IWM",   # iShares Russell 2000
    "VEA",   # Vanguard FTSE Developed Markets
    "VWO",   # Vanguard FTSE Emerging Markets
    "BND",   # Vanguard Total Bond Market
    "GLD",   # SPDR Gold Shares
    "SLV",   # iShares Silver Trust
    "TLT",   # iShares 20+ Year Treasury
    "EEM",   # iShares MSCI Emerging Markets
    "DIA",   # SPDR Dow Jones Industrial Average
})


def is_etf_ticker(ticker: str, exchange_code: str = "") -> bool:
    """粗略判断给定 ticker 是否可能为 ETF。

    判定规则：
    - 6 位 A 股代码：5 开头且在上海 → ETF；159 开头且在深圳 → ETF
    - 港股 / 美股：以 ``_KNOWN_HK_ETFS`` / ``_KNOWN_US_ETFS`` whitelist 判定
    - 其他形态默认 False
    """
    if not ticker:
        return False
    code = str(ticker).strip()
    exchange_short = normalize_exchange_code(exchange_code)

    # 港股 / 美股 ETF：whitelist 判定（避免把 0700 / AAPL 等个股误识别）
    # 港股代码先去前导零归一化（'3032' / '03032' 都应命中白名单）
    if exchange_short == "HK" and code.isdigit() and str(int(code)) in _KNOWN_HK_ETFS:
        return True
    if exchange_short == "US" and code.upper() in _KNOWN_US_ETFS:
        return True

    if not code.isdigit():
        return False
    if len(code) != 6:
        return False
    if exchange_short == "SH":
        return code.startswith(_ETF_SHANGHAI_PREFIXES)
    if exchange_short == "SZ":
        return code.startswith(_ETF_SHENZHEN_PREFIXES)
    # 未知交易所：结合两个集合的命中情况
    if code.startswith(_ETF_SHANGHAI_PREFIXES) or code.startswith(_ETF_SHENZHEN_PREFIXES):
        # 进一步区分：5 开头且 510/511/512/515/516/517/518/588 多为 ETF；159 多为 ETF
        return True
    return False


def detect_security_type(ticker: str, exchange_code: str = "") -> str:
    """根据 ticker + exchange_code 推断证券类型（'ETF' 或 'STOCK'）。"""
    return "ETF" if is_etf_ticker(ticker, exchange_code) else "STOCK"

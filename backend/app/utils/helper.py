def determine_country(code: str) -> tuple[str, str]:
    """
    根据代码判断所属国家/地区。

    - 如果是6位数字代码，返回数字代码和CHN
    - 如果是小于6位的数字代码，返回移除前导0的数字代码和HKG
    - 如果非数字代码，返回代码和USA

    Args:
        code (str): 输入的代码

    Returns:
        tuple[str, str]: (处理后的代码, 国家代码)
    """
    if code.isdigit():
        if len(code) == 6:
            return code, 'CHN'
        elif len(code) < 6:
            # 前面补0 到至少4位
            processed_code = str(int(code)).zfill(4)
            return processed_code, 'HKG'
    # 非数字代码
    return code, 'USA'


# 场外基金(开放式基金)标记：
# 场外基金代码为 6 位数字，与场内个股 / ETF / 指数的代码空间高度重叠
# （例如 000001 既是上证指数、也是华夏成长混合等多只场外基金），无法从代码本身区分。
# 因此约定：在代码「开头或结尾」额外加一个字母 F(Fund) 或 O(OTC) 来标记场外基金。
#   例：F007339 / 007339F / O007339 / 007339O 均表示场外基金 007339。
# 仅当去掉首/尾标记字母后剩余恰好为 6 位数字时才认定为场外基金，
# 避免误伤美股纯字母代码（如 F=福特、AAPL）。
OTC_FUND_MARKERS = ("F", "O")


def parse_otc_marker(code: str) -> tuple[str, bool]:
    """识别并剥离场外基金标记。

    Args:
        code: 用户输入的原始代码（可能带首/尾标记字母）

    Returns:
        tuple[str, bool]: (剥离标记后的代码, 是否为场外基金)
    """
    raw = (code or "").strip().upper()
    # 标记(1位字母) + 6位数字 = 7 位
    if len(raw) == 7:
        if raw[0] in OTC_FUND_MARKERS and raw[1:].isdigit():
            return raw[1:], True
        if raw[-1] in OTC_FUND_MARKERS and raw[:-1].isdigit():
            return raw[:-1], True
    return raw, False


def resolve_ticker(code: str) -> tuple[str, str, str]:
    """统一解析用户输入代码：处理场外基金标记 + 判定国家/地区。

    Args:
        code: 用户输入的原始代码

    Returns:
        tuple[str, str, str]: (标准代码, 国家代码, 证券类型提示)
          - 标准代码：已剥离场外基金标记
          - 证券类型提示：'FUND' 表示场外基金；'' 表示交由后续分类逻辑判断
    """
    clean, is_otc = parse_otc_marker(code)
    resolved_code, country = determine_country(clean)
    return resolved_code, country, ("FUND" if is_otc else "")

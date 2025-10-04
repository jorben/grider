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
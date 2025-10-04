"""
简洁的参数验证工具
提供简单易用的验证函数，便于扩展各接口的参数校验
"""
from typing import Any, Dict, List, Optional, Callable, Tuple


def validate_required(data: Dict[str, Any], fields: List[str]) -> Optional[Tuple[Dict, int]]:
    """
    验证必填字段
    
    Args:
        data: 要验证的数据字典
        fields: 必填字段列表
    
    Returns:
        如果验证失败返回错误响应和状态码，否则返回None
    """
    missing_fields = [field for field in fields if field not in data or data[field] is None]
    if missing_fields:
        return {
            'error': f'缺少必填字段：{", ".join(missing_fields)}',
            'missing_fields': missing_fields
        }, 400
    return None


def validate_string(data: Dict[str, Any], field: str, min_length: int = 1, max_length: Optional[int] = None) -> Optional[Tuple[Dict, int]]:
    """
    验证字符串字段
    
    Args:
        data: 要验证的数据字典
        field: 字段名
        min_length: 最小长度
        max_length: 最大长度
    
    Returns:
        如果验证失败返回错误响应和状态码，否则返回None
    """
    if field in data and data[field] is not None:
        value = str(data[field])
        if len(value) < min_length:
            return {
                'error': f'字段 "{field}" 至少需要 {min_length} 个字符'
            }, 400
        if max_length and len(value) > max_length:
            return {
                'error': f'字段 "{field}" 最多只能有 {max_length} 个字符'
            }, 400
    return None


def validate_integer(data: Dict[str, Any], field: str, min_value: Optional[int] = None, max_value: Optional[int] = None) -> Optional[Tuple[Dict, int]]:
    """
    验证整数字段
    
    Args:
        data: 要验证的数据字典
        field: 字段名
        min_value: 最小值
        max_value: 最大值
    
    Returns:
        如果验证失败返回错误响应和状态码，否则返回None
    """
    if field in data and data[field] is not None:
        try:
            value = int(data[field])
            if min_value is not None and value < min_value:
                return {
                    'error': f'字段 "{field}" 必须至少为 {min_value}'
                }, 400
            if max_value is not None and value > max_value:
                return {
                    'error': f'字段 "{field}" 必须最多为 {max_value}'
                }, 400
        except (ValueError, TypeError):
            return {
                'error': f'字段 "{field}" 必须是整数'
            }, 400
    return None

def validate_float(data: Dict[str, Any], field: str, min_value: Optional[float] = None, max_value: Optional[float] = None) -> Optional[Tuple[Dict, int]]:
    """
    验证浮点数字段

    Args:
        data: 要验证的数据字典
        field: 字段名
        min_value: 最小值
        max_value: 最大值

    Returns:
        如果验证失败返回错误响应和状态码，否则返回None
    """
    if field in data and data[field] is not None:
        try:
            value = float(data[field])
            if min_value is not None and value < min_value:
                return {
                    'error': f'字段 "{field}" 必须至少为 {min_value}'
                }, 400
            if max_value is not None and value > max_value:
                return {
                    'error': f'字段 "{field}" 必须最多为 {max_value}'
                }, 400
        except (ValueError, TypeError):
            return {
                'error': f'字段 "{field}" 必须是浮点数'
            }, 400
    return None


def validate_enum(data: Dict[str, Any], field: str, enum_values: List[Any]) -> Optional[Tuple[Dict, int]]:
    """
    验证枚举字段

    Args:
        data: 要验证的数据字典
        field: 字段名
        enum_values: 允许的值列表

    Returns:
        如果验证失败返回错误响应和状态码，否则返回None
    """
    if field in data and data[field] is not None:
        if data[field] not in enum_values:
            return {
                'error': f'字段 "{field}" 必须是以下之一：{", ".join(map(str, enum_values))}'
            }, 400
    return None


def validate_email(data: Dict[str, Any], field: str) -> Optional[Tuple[Dict, int]]:
    """
    验证邮箱格式
    
    Args:
        data: 要验证的数据字典
        field: 字段名
    
    Returns:
        如果验证失败返回错误响应和状态码，否则返回None
    """
    if field in data and data[field] is not None:
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, str(data[field])):
            return {
                'error': f'字段 "{field}" 必须是有效的电子邮件地址'
            }, 400
    return None


def validate_custom(data: Dict[str, Any], field: str, validator_func: Callable[[Any], bool], error_message: str) -> Optional[Tuple[Dict, int]]:
    """
    自定义验证
    
    Args:
        data: 要验证的数据字典
        field: 字段名
        validator_func: 验证函数
        error_message: 错误消息
    
    Returns:
        如果验证失败返回错误响应和状态码，否则返回None
    """
    if field in data and data[field] is not None:
        if not validator_func(data[field]):
            return {
                'error': error_message
            }, 400
    return None


def validate_all(data: Dict[str, Any], rules: List[Dict]) -> Optional[Tuple[Dict, int]]:
    """
    批量验证多个规则

    Args:
        data: 要验证的数据字典
        rules: 验证规则列表，每个规则包含:
            - type: 验证类型 ('required', 'string', 'integer', 'float', 'enum', 'email', 'custom')
            - field: 字段名
            - 其他参数根据验证类型而定

    Returns:
        如果验证失败返回错误响应和状态码，否则返回None
    """
    for rule in rules:
        rule_type = rule['type']
        field = rule['field']
        
        if rule_type == 'required':
            result = validate_required(data, [field])
        elif rule_type == 'string':
            result = validate_string(data, field, rule.get('min_length', 1), rule.get('max_length'))
        elif rule_type == 'integer':
            result = validate_integer(data, field, rule.get('min_value'), rule.get('max_value'))
        elif rule_type == 'float':
            result = validate_float(data, field, rule.get('min_value'), rule.get('max_value'))
        elif rule_type == 'enum':
            result = validate_enum(data, field, rule['enum_values'])
        elif rule_type == 'email':
            result = validate_email(data, field)
        elif rule_type == 'custom':
            result = validate_custom(data, field, rule['validator_func'], rule['error_message'])
        else:
            continue
        
        if result:
            return result
    
    return None


# 预定义的验证规则集合
VALIDATION_RULES = {
    'user_name': [
        {'type': 'required', 'field': 'name'},
        {'type': 'string', 'field': 'name', 'min_length': 1, 'max_length': 100}
    ],
    
    'user_email': [
        {'type': 'required', 'field': 'email'},
        {'type': 'email', 'field': 'email'}
    ],
    
    'pagination': [
        {'type': 'integer', 'field': 'page', 'min_value': 1},
        {'type': 'integer', 'field': 'per_page', 'min_value': 1, 'max_value': 100}
    ]
}


def validate_with_rules(data: Dict[str, Any], rule_set: str) -> Optional[Tuple[Dict, int]]:
    """
    使用预定义规则集进行验证
    
    Args:
        data: 要验证的数据字典
        rule_set: 规则集名称
    
    Returns:
        如果验证失败返回错误响应，否则返回None
    """
    if rule_set in VALIDATION_RULES:
        return validate_all(data, VALIDATION_RULES[rule_set])
    return None


# 装饰器版本（支持多种请求类型）
def validate_request(rules: List[Dict], data_source: str = 'json'):
    """
    验证请求数据的装饰器，支持多种数据源
    
    Args:
        rules: 验证规则列表
        data_source: 数据源类型 ('json', 'form', 'args', 'headers', 'combined')
    
    Returns:
        装饰器函数
    """
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request, jsonify
            
            # 根据数据源获取数据
            if data_source == 'json':
                data = request.get_json() or {}
            elif data_source == 'form':
                data = request.form.to_dict()
            elif data_source == 'args':
                data = request.args.to_dict()
            elif data_source == 'headers':
                data = dict(request.headers)
            elif data_source == 'combined':
                # 合并多种数据源（优先级：json > form > args）
                data = {}
                data.update(request.args.to_dict())
                data.update(request.form.to_dict())
                json_data = request.get_json() or {}
                data.update(json_data)
            else:
                data = {}
            
            # 执行验证
            result = validate_all(data, rules)
            if result:
                return jsonify(result[0]), result[1]
            
            # 将验证后的数据传递给路由函数
            kwargs['validated_data'] = data
            return func(*args, **kwargs)
        return wrapper
    return decorator


# 快捷装饰器
def validate_json(rules: List[Dict]):
    """验证JSON请求体的快捷装饰器"""
    return validate_request(rules, data_source='json')


def validate_form(rules: List[Dict]):
    """验证表单数据的快捷装饰器"""
    return validate_request(rules, data_source='form')


def validate_query(rules: List[Dict]):
    """验证查询参数的快捷装饰器"""
    return validate_request(rules, data_source='args')


def validate_headers(rules: List[Dict]):
    """验证请求头的快捷装饰器"""
    return validate_request(rules, data_source='headers')


def validate_combined(rules: List[Dict]):
    """验证合并数据源的快捷装饰器（优先级：json > form > args）"""
    return validate_request(rules, data_source='combined')
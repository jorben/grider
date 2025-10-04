"""
请求日志中间件
记录所有HTTP请求和响应信息，支持请求ID追踪和敏感信息过滤
"""
import os
import time
import uuid
import json
from typing import Dict, Any, Optional
from flask import Flask, g, request, jsonify
from werkzeug.exceptions import HTTPException


# 敏感字段黑名单
SENSITIVE_FIELDS = {
    'password', 'passwd', 'pwd',
    'secret', 'token', 'api_key', 'apikey',
    'authorization', 'auth',
    'credit_card', 'cvv', 'ssn',
    'private_key', 'public_key'
}


def filter_sensitive_data(data: Any) -> Any:
    """
    递归过滤敏感字段
    
    Args:
        data: 需要过滤的数据（字典、列表或其他类型）
        
    Returns:
        过滤敏感信息后的数据
    """
    if isinstance(data, dict):
        filtered = {}
        for key, value in data.items():
            if key.lower() in SENSITIVE_FIELDS:
                filtered[key] = '[FILTERED]'
            else:
                filtered[key] = filter_sensitive_data(value)
        return filtered
    elif isinstance(data, list):
        return [filter_sensitive_data(item) for item in data]
    else:
        return data


def get_client_ip() -> str:
    """
    获取客户端真实IP地址
    
    Returns:
        客户端IP地址
    """
    # 检查代理头
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr or 'unknown'


def extract_request_data() -> Dict[str, Any]:
    """
    提取请求数据
    
    Returns:
        包含请求信息的字典
    """
    data = {
        'method': request.method,
        'path': request.path,
        'query_params': dict(request.args),
        'client_ip': get_client_ip(),
        'user_agent': request.headers.get('User-Agent', 'unknown'),
    }
    
    # 添加查询字符串
    if request.query_string:
        data['query_string'] = request.query_string.decode('utf-8')
    
    # 添加请求头（如果启用）
    if os.getenv('REQUEST_LOG_HEADERS', 'true').lower() == 'true':
        data['headers'] = dict(request.headers)
    
    # 添加请求体（如果启用且是JSON）
    if (os.getenv('REQUEST_LOG_BODY', 'true').lower() == 'true' and 
        request.is_json and request.get_json(silent=True)):
        data['body'] = filter_sensitive_data(request.get_json())
    
    return data


def before_request_handler():
    """
    请求开始前的处理函数
    生成请求ID并记录开始时间
    """
    # 生成唯一请求ID
    request_id = str(uuid.uuid4())
    
    # 存储到Flask的g对象中
    g.request_id = request_id
    g.start_time = time.time()
    
    # 提取请求数据
    request_data = extract_request_data()
    
    # 记录请求开始日志
    app = current_app if 'current_app' in globals() else Flask(__name__)
    app.logger.info(
        f"HTTP Request - {request.method} {request.path}",
        extra={
            'request_id': request_id,
            'method': request.method,
            'path': request.path,
            'query_params': request_data.get('query_params', {}),
            'client_ip': request_data['client_ip'],
            'user_agent': request_data['user_agent']
        }
    )


def after_request_handler(response):
    """
    请求完成后的处理函数
    计算处理时间并记录完整日志
    
    Args:
        response: Flask响应对象
        
    Returns:
        响应对象（添加请求ID头）
    """
    # 检查是否启用请求日志
    if os.getenv('ENABLE_REQUEST_LOGGING', 'true').lower() != 'true':
        return response
    
    # 获取请求ID和开始时间
    request_id = getattr(g, 'request_id', 'unknown')
    start_time = getattr(g, 'start_time', time.time())
    
    # 计算处理时间（毫秒）
    duration_ms = round((time.time() - start_time) * 1000, 2)
    
    # 获取响应大小（避免在direct passthrough模式下调用get_data）
    try:
        response_data = response.get_data()
        response_size = len(response_data) if response_data else 0
    except RuntimeError:
        # direct passthrough模式，无法获取数据大小
        response_size = 0
    
    # 提取请求数据
    request_data = extract_request_data()
    
    # 构建日志数据
    log_data = {
        'request_id': request_id,
        'method': request.method,
        'path': request.path,
        'query_params': request_data.get('query_params', {}),
        'client_ip': request_data['client_ip'],
        'user_agent': request_data['user_agent'],
        'status_code': response.status_code,
        'duration_ms': duration_ms,
        'response_size': response_size
    }
    
    # 添加请求头（如果启用）
    if 'headers' in request_data:
        log_data['headers'] = request_data['headers']
    
    # 添加请求体（如果启用）
    if 'body' in request_data:
        log_data['body'] = request_data['body']
    
    # 添加响应体（如果启用且是JSON）
    if (os.getenv('REQUEST_LOG_RESPONSE_BODY', 'false').lower() == 'true' and
        response.content_type and 'application/json' in response.content_type):
        try:
            # 获取响应数据
            response_data = response.get_data()
            if response_data:
                # 尝试解析JSON
                try:
                    json_data = json.loads(response_data.decode('utf-8'))
                    log_data['response_body'] = filter_sensitive_data(json_data)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # 如果不是JSON，记录原始数据（限制长度）
                    response_str = response_data.decode('utf-8', errors='ignore')
                    if len(response_str) > 200:
                        response_str = response_str[:200] + "..."
                    log_data['response_body'] = response_str
        except Exception:
            pass  # 忽略获取响应数据错误
    
    # 确定日志级别
    log_level = 'info'
    if response.status_code >= 500:
        log_level = 'error'
    elif response.status_code >= 400:
        log_level = 'warning'
    elif duration_ms > 1000:  # 超过1秒的慢请求
        log_level = 'warning'
    
    # 记录日志
    app = current_app if 'current_app' in globals() else Flask(__name__)
    logger_method = getattr(app.logger, log_level)
    
    # 构建详细的消息
    message_parts = [
        f"HTTP Response - {request.method} {request.path} [{response.status_code}] - {duration_ms}ms"
    ]
    
    logger_method(" - ".join(message_parts), extra=log_data)
    
    # 添加请求ID到响应头
    response.headers['X-Request-ID'] = request_id
    
    return response


def init_request_logging(app: Flask):
    """
    初始化请求日志中间件
    
    Args:
        app: Flask应用实例
    """
    # 检查是否启用请求日志
    if os.getenv('ENABLE_REQUEST_LOGGING', 'true').lower() != 'true':
        app.logger.info("请求日志中间件已禁用")
        return app
    
    # 注册请求钩子
    app.before_request(before_request_handler)
    app.after_request(after_request_handler)
    
    # 设置全局current_app引用（用于在钩子函数中访问app）
    global current_app
    current_app = app
    
    app.logger.info(
        f"请求日志中间件已初始化 - "
        f"记录请求体: {os.getenv('REQUEST_LOG_BODY', 'true')}, "
        f"记录请求头: {os.getenv('REQUEST_LOG_HEADERS', 'true')}, "
        f"记录响应体: {os.getenv('REQUEST_LOG_RESPONSE_BODY', 'false')}"
    )
    
    return app


# 全局变量存储当前应用实例
current_app = None
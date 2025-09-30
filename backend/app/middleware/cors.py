"""
CORS中间件配置
提供跨域资源共享支持
"""

from flask_cors import CORS
import os


def setup_cors(app):
    """
    配置CORS中间件
    
    Args:
        app: Flask应用实例
    """
    # 从环境变量获取CORS配置，支持灵活配置
    cors_origins = os.getenv('CORS_ORIGINS', '*')
    cors_methods = os.getenv('CORS_METHODS', 'GET,POST,PUT,DELETE,OPTIONS')
    cors_headers = os.getenv('CORS_HEADERS', 'Content-Type,Authorization')
    cors_supports_credentials = os.getenv('CORS_SUPPORTS_CREDENTIALS', 'false').lower() == 'true'
    
    # 解析origins配置
    if cors_origins == '*':
        origins = ['*']
    else:
        origins = [origin.strip() for origin in cors_origins.split(',')]
    
    # 解析methods配置
    methods = [method.strip() for method in cors_methods.split(',')]
    
    # 解析headers配置  
    headers = [header.strip() for header in cors_headers.split(',')]
    
    # 配置CORS
    CORS(
        app,
        origins=origins,
        methods=methods,
        allow_headers=headers,
        supports_credentials=cors_supports_credentials,
        expose_headers=['Content-Disposition'],
        max_age=3600  # 1小时缓存
    )
    
    return app


def get_cors_config():
    """
    获取当前CORS配置信息
    
    Returns:
        dict: CORS配置信息
    """
    return {
        'origins': os.getenv('CORS_ORIGINS', '*'),
        'methods': os.getenv('CORS_METHODS', 'GET,POST,PUT,DELETE,OPTIONS'),
        'headers': os.getenv('CORS_HEADERS', 'Content-Type,Authorization'),
        'supports_credentials': os.getenv('CORS_SUPPORTS_CREDENTIALS', 'false').lower() == 'true'
    }
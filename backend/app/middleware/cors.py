"""CORS中间件配置"""
import os
from flask_cors import CORS


def init_cors(app):
    """初始化CORS中间件"""
    
    # 从环境变量获取允许的源
    allowed_origins = os.getenv('CORS_ORIGINS', '*').split(',')
    allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]
    
    # CORS配置
    cors_config = {
        'origins': allowed_origins,
        'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
        'allow_headers': [
            'Content-Type', 
            'Authorization', 
            'X-Requested-With',
            'X-CSRF-Token',
            'Accept',
            'Origin'
        ],
        'expose_headers': [
            'Content-Type',
            'X-Total-Count',
            'X-Page-Count'
        ],
        'supports_credentials': True,
        'max_age': 86400  # 24小时预检缓存
    }
    
    # 根据环境调整配置
    if app.config.get('ENV') == 'production':
        # 生产环境更严格的配置
        cors_config['origins'] = allowed_origins if allowed_origins != ['*'] else []
        cors_config['supports_credentials'] = True
    
    # 初始化CORS
    CORS(app, **cors_config)
    
    app.logger.info(f"CORS中间件已初始化 - 允许源: {allowed_origins}")
    
    return app


def get_cors_config():
    """获取当前CORS配置"""
    return {
        'allowed_origins': os.getenv('CORS_ORIGINS', '*').split(','),
        'allowed_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
        'allowed_headers': [
            'Content-Type', 
            'Authorization', 
            'X-Requested-With',
            'X-CSRF-Token',
            'Accept',
            'Origin'
        ],
        'supports_credentials': True,
        'max_age': 86400
    }
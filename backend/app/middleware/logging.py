"""
日志配置中间件
支持区分生产环境和开发环境的日志配置
提供请求日志记录和结构化日志输出
"""

import os
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, request, g
from app.constants import (
    ENV_DEVELOPMENT, ENV_PRODUCTION, ENV_TESTING,
    LOG_LEVEL_DEBUG, LOG_LEVEL_INFO, LOG_LEVEL_WARNING, LOG_LEVEL_ERROR, LOG_LEVEL_CRITICAL,
    LOG_FORMAT_SIMPLE, LOG_FORMAT_DETAILED,
    HTTP_OK, HTTP_BAD_REQUEST, HTTP_INTERNAL_SERVER_ERROR
)


class LoggingConfig:
    """日志配置类"""
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask) -> None:
        """初始化日志配置"""
        # 获取环境配置
        env = os.getenv('FLASK_ENV', ENV_DEVELOPMENT)
        
        # 配置日志级别
        log_level = self._get_log_level(env)
        log_format = self._get_log_format(env)
        
        # 清除现有的处理器
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # 配置根日志记录器
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.StreamHandler(),  # 控制台输出
            ]
        )
        
        # 配置Flask应用日志记录器
        app.logger.setLevel(log_level)
        
        # 移除Flask默认的处理器，使用我们的配置
        for handler in app.logger.handlers[:]:
            app.logger.removeHandler(handler)
        
        # 添加我们的处理器
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(log_format))
        app.logger.addHandler(handler)
        
        # 设置其他重要日志记录器的级别
        logging.getLogger('werkzeug').setLevel(
            LOG_LEVEL_INFO if env == ENV_PRODUCTION else LOG_LEVEL_WARNING
        )
        logging.getLogger('sqlalchemy.engine').setLevel(
            LOG_LEVEL_WARNING if env == ENV_PRODUCTION else LOG_LEVEL_INFO
        )
        
        app.logger.info(f"Logging configured for {env} environment with level {log_level}")
    
    def _get_log_level(self, env: str) -> int:
        """根据环境获取日志级别"""
        level_map = {
            ENV_DEVELOPMENT: LOG_LEVEL_DEBUG,
            ENV_TESTING: LOG_LEVEL_INFO,
            ENV_PRODUCTION: LOG_LEVEL_WARNING
        }
        
        # 允许通过环境变量覆盖默认级别
        env_level = os.getenv('LOG_LEVEL')
        if env_level and env_level.upper() in [LOG_LEVEL_DEBUG, LOG_LEVEL_INFO, 
                                             LOG_LEVEL_WARNING, LOG_LEVEL_ERROR, LOG_LEVEL_CRITICAL]:
            return getattr(logging, env_level.upper())
        
        return getattr(logging, level_map.get(env, LOG_LEVEL_INFO))
    
    def _get_log_format(self, env: str) -> str:
        """根据环境获取日志格式"""
        if env == ENV_PRODUCTION:
            return LOG_FORMAT_SIMPLE
        else:
            return LOG_FORMAT_DETAILED


class RequestLogger:
    """请求日志记录器"""
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask) -> None:
        """初始化请求日志记录器"""
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_request(self._teardown_request)
    
    def _before_request(self) -> None:
        """请求开始前的处理"""
        g.start_time = time.time()
        g.request_id = self._generate_request_id()
        
        # 记录请求开始
        if request.endpoint and request.endpoint != 'static':
            logging.info(
                f"Request started - ID: {g.request_id}, "
                f"Method: {request.method}, Path: {request.path}, "
                f"IP: {request.remote_addr}"
            )
    
    def _after_request(self, response) -> None:
        """请求结束后的处理"""
        if hasattr(g, 'start_time') and hasattr(g, 'request_id'):
            duration = time.time() - g.start_time
            
            # 根据状态码确定日志级别
            if response.status_code >= HTTP_INTERNAL_SERVER_ERROR:
                log_level = logging.ERROR
            elif response.status_code >= HTTP_BAD_REQUEST:
                log_level = logging.WARNING
            else:
                log_level = logging.INFO
            
            # 记录请求完成
            logging.log(
                log_level,
                f"Request completed - ID: {g.request_id}, "
                f"Method: {request.method}, Path: {request.path}, "
                f"Status: {response.status_code}, Duration: {duration:.3f}s"
            )
        
        return response
    
    def _teardown_request(self, exception) -> None:
        """请求清理处理"""
        if exception is not None:
            logging.error(
                f"Request error - ID: {getattr(g, 'request_id', 'unknown')}, "
                f"Method: {request.method}, Path: {request.path}, "
                f"Error: {str(exception)}",
                exc_info=True
            )
    
    def _generate_request_id(self) -> str:
        """生成请求ID"""
        import uuid
        return str(uuid.uuid4())[:8]


class StructuredLogger:
    """结构化日志记录器"""
    
    @staticmethod
    def debug(message: str, **kwargs) -> None:
        """记录调试日志"""
        logging.debug(_format_structured_message(message, **kwargs))
    
    @staticmethod
    def info(message: str, **kwargs) -> None:
        """记录信息日志"""
        logging.info(_format_structured_message(message, **kwargs))
    
    @staticmethod
    def warning(message: str, **kwargs) -> None:
        """记录警告日志"""
        logging.warning(_format_structured_message(message, **kwargs))
    
    @staticmethod
    def error(message: str, **kwargs) -> None:
        """记录错误日志"""
        logging.error(_format_structured_message(message, **kwargs))
    
    @staticmethod
    def critical(message: str, **kwargs) -> None:
        """记录严重错误日志"""
        logging.critical(_format_structured_message(message, **kwargs))
    
    @staticmethod
    def request_log(level: str, message: str, request_data: Dict[str, Any]) -> None:
        """记录请求相关日志"""
        log_func = getattr(logging, level.lower())
        log_func(_format_request_message(message, request_data))


def _format_structured_message(message: str, **kwargs) -> str:
    """格式化结构化日志消息"""
    if not kwargs:
        return message
    
    details = ' '.join([f'{k}={v}' for k, v in kwargs.items()])
    return f"{message} | {details}"


def _format_request_message(message: str, request_data: Dict[str, Any]) -> str:
    """格式化请求日志消息"""
    details = []
    
    if 'method' in request_data:
        details.append(f"method={request_data['method']}")
    if 'path' in request_data:
        details.append(f"path={request_data['path']}")
    if 'status_code' in request_data:
        details.append(f"status={request_data['status_code']}")
    if 'duration' in request_data:
        details.append(f"duration={request_data['duration']:.3f}s")
    if 'ip' in request_data:
        details.append(f"ip={request_data['ip']}")
    if 'user_agent' in request_data:
        details.append(f"ua={request_data['user_agent']}")
    
    return f"{message} | {' '.join(details)}"


def setup_logging(app: Flask) -> Flask:
    """
    配置日志中间件
    
    Args:
        app: Flask应用实例
        
    Returns:
        Flask: 配置了日志中间件的应用实例
    """
    # 初始化日志配置
    logging_config = LoggingConfig(app)
    
    # 初始化请求日志记录器
    request_logger = RequestLogger(app)
    
    # 记录应用启动信息
    app.logger.info("Logging middleware configured successfully")
    
    return app


# 导出模块内容
__all__ = [
    'LoggingConfig',
    'RequestLogger', 
    'StructuredLogger',
    'setup_logging'
]
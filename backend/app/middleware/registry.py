"""
中间件注册器
统一管理所有中间件的注册和配置
"""

from typing import List, Callable, Dict, Any
from flask import Flask
import logging

# 中间件注册表
_middleware_registry: List[Callable[[Flask], Flask]] = []


def register_middleware(middleware_func: Callable[[Flask], Flask]) -> None:
    """
    注册中间件函数
    
    Args:
        middleware_func: 中间件函数，接收Flask应用并返回配置后的应用
    """
    _middleware_registry.append(middleware_func)
    logging.debug(f"Middleware registered: {middleware_func.__name__}")


def register_middlewares(app: Flask) -> Flask:
    """
    注册所有已配置的中间件
    
    Args:
        app: Flask应用实例
        
    Returns:
        Flask: 配置了所有中间件的应用实例
    """
    if not _middleware_registry:
        logging.warning("No middlewares registered")
        return app
    
    # 按注册顺序应用中间件
    for middleware_func in _middleware_registry:
        try:
            app = middleware_func(app)
            logging.info(f"Middleware applied successfully: {middleware_func.__name__}")
        except Exception as e:
            logging.error(f"Failed to apply middleware {middleware_func.__name__}: {e}")
            # 继续应用其他中间件，不中断启动
            continue
    
    return app


def get_registered_middlewares() -> List[str]:
    """
    获取已注册的中间件列表
    
    Returns:
        List[str]: 中间件函数名列表
    """
    return [func.__name__ for func in _middleware_registry]


def clear_middleware_registry() -> None:
    """
    清空中间件注册表（主要用于测试）
    """
    _middleware_registry.clear()
    logging.debug("Middleware registry cleared")


# 自动注册CORS中间件
from .cors import setup_cors
register_middleware(setup_cors)
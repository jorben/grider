"""
中间件模块
提供各种中间件功能，包括CORS、认证、日志等
"""

from .cors import setup_cors
from .registry import register_middlewares

__all__ = ['setup_cors', 'register_middlewares']
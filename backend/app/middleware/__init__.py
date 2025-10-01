"""中间件模块初始化"""


# 初始化中间件
from .cors import init_cors
from .request_logging import init_request_logging

def register(app):
    # 初始化CORS中间件
    init_cors(app)
    
    # 初始化请求日志中间件
    init_request_logging(app)

"""中间件模块初始化"""


# 初始化中间件
from .cors import init_cors

def register(app):
    # 初始化CORS中间件
    init_cors(app)

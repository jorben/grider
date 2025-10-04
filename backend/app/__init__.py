import os
from flask import Flask, send_from_directory, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入日志配置
from app.utils.logger import setup_logger

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():

# 根据环境变量决定静态文件配置
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    if FLASK_ENV == 'production':
        # 生产环境：配置静态文件服务
        app = Flask(__name__,
                    static_folder='../../static',
                    static_url_path='/static')
        app.logger.info("生产环境模式：启用静态文件服务")
    else:
        # 开发环境：不处理静态文件（前端独立运行）
        app = Flask(__name__)
        app.logger.info("开发环境模式：仅提供API服务")
    
    # 配置
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['ENV'] = FLASK_ENV
    
    # 配置日志系统（在所有其他初始化之前）
    setup_logger(app)
    app.logger.info('Flask应用初始化开始')
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    app.logger.info('数据库和JWT扩展初始化完成')

    # 注册中间件
    from app.middleware import register as middle_register
    middle_register(app)
    app.logger.info('中间件注册完成')
    
    # 注册蓝图
    from app.routes import register as bp_register
    bp_register(app)
    app.logger.info('蓝图注册完成')

    # 只在生产环境添加静态文件路由
    if FLASK_ENV == 'production':
        setup_static_routes(app)
    
    app.logger.info('Flask应用初始化完成')
    return app

def setup_static_routes(app):
    """设置静态文件路由（仅生产环境）"""
    
    @app.route('/')
    def serve_index():
        """服务前端主页"""
        try:
            return send_file('../../static/index.html')
        except FileNotFoundError:
            app.logger.error("静态文件 index.html 不存在")
            return {
                'success': False,
                'error': '前端文件未找到，请检查构建是否完成'
            }, 404
    
    @app.route('/<path:path>')
    def serve_spa_routes(path):
        """服务SPA路由（非API和静态文件路径）"""
        # 如果是API路由或静态文件路由，跳过
        if path.startswith('api/'):
            return None

        # 定义前端路由路径（这些路径应该返回 index.html）
        frontend_routes = ['analysis', 'dashboard', 'settings', 'help']

        # 检查是否是前端路由
        if any(path.startswith(route) for route in frontend_routes):
            try:
                return send_file('../../static/index.html')
            except FileNotFoundError:
                app.logger.error("静态文件 index.html 不存在")
                return {
                    'success': False,
                    'error': '前端文件未找到'
                }, 404
        
        # 尝试提供静态文件
        try:
            return send_from_directory('../../static', path)
        except FileNotFoundError:
            # 文件不存在时返回index.html（支持其他前端路由）
            try:
                return send_file('../../static/index.html')
            except FileNotFoundError:
                app.logger.error("静态文件 index.html 不存在")
                return {
                    'success': False,
                    'error': '前端文件未找到'
                }, 404

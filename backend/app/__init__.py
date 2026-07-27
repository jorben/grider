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
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development').strip().lower()
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
    """设置静态文件路由（仅生产环境）

    使用基于模块位置的绝对路径，避免依赖当前工作目录（CWD）。
    静态目录为 项目根/static （即 backend 的上一级目录下的 static）。
    """
    # backend/app/__init__.py -> backend/app -> backend -> 项目根
    _project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    static_dir = os.path.join(_project_root, 'static')
    index_file = os.path.join(static_dir, 'index.html')

    def _serve_index():
        if os.path.exists(index_file):
            return send_file(index_file)
        app.logger.error(f"静态文件 index.html 不存在: {index_file}")
        return {
            'success': False,
            'message': '前端文件未找到，请检查构建是否完成（static/index.html）'
        }, 404

    @app.route('/')
    def serve_index():
        """服务前端主页"""
        return _serve_index()

    @app.route('/<path:path>')
    def serve_spa_routes(path):
        """服务SPA路由（非API和静态文件路径）"""
        # 如果是API路由，跳过
        if path.startswith('api/'):
            return None

        # 定义前端路由路径（这些路径应该返回 index.html）
        frontend_routes = ['analysis', 'dashboard', 'settings', 'help', 'screener', 'ma-backtest', 'ma-screener', 'ma-compare', 'grid-compare', 'fish-basin']

        # 检查是否是前端路由
        if any(path.startswith(route) for route in frontend_routes):
            return _serve_index()

        # 尝试提供静态文件（绝对目录）
        file_path = os.path.join(static_dir, path)
        if os.path.isfile(file_path):
            return send_from_directory(static_dir, path)

        # 文件不存在时返回 index.html（支持前端路由刷新）
        return _serve_index()

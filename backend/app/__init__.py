import os
from flask import Flask
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

# 导入常量模块
from . import constants

def create_app():
    app = Flask(__name__)
    
    # 配置
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['ENV'] = os.getenv('FLASK_ENV', 'development')
    
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
    
    app.logger.info('Flask应用初始化完成')
    return app
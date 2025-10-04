import os
import argparse
from app import create_app
from flask_migrate import upgrade as migrate_upgrade
from app.constants import APP_VERSION

app = create_app()

def auto_migrate():
    """自动检测并应用数据库迁移"""
    app.logger.info("=== Auto Migration Check ===")
    with app.app_context():
        try:
            # 直接尝试应用迁移
            app.logger.info("Applying database migrations...")
            migrate_upgrade()
            app.logger.info("Database migrations applied successfully!")
            
        except Exception as e:
            app.logger.error(f"Migration error: {e}")
            app.logger.error("Please check the migration configuration.")

if __name__ == "__main__":
    # 应用启动时自动执行迁移
    auto_migrate()
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='ETF网格交易策略分析系统')
    parser.add_argument('--port', type=int, default=None, help='服务器端口号')
    parser.add_argument('--host', type=str, default=None, help='服务器主机地址')
    args = parser.parse_args()
    
    # 优先级：命令行参数 > 环境变量 > 默认值
    port = args.port or int(os.environ.get('FLASK_PORT', 5000))
    host = args.host or str(os.environ.get('FLASK_HOST', '0.0.0.0'))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.logger.info(f"启动网格交易策略分析系统，版本: {APP_VERSION}, 服务地址: {host}:{port}")
    app.run(host=host, port=port, debug=debug)

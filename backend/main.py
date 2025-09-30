from app import create_app
from flask_migrate import upgrade as migrate_upgrade

app = create_app()

def auto_migrate():
    """自动检测并应用数据库迁移"""
    print("=== Auto Migration Check ===")
    with app.app_context():
        try:
            # 直接尝试应用迁移
            print("Applying database migrations...")
            migrate_upgrade()
            print("Database migrations applied successfully!")
            
        except Exception as e:
            print(f"Migration error: {e}")
            print("Please check the migration configuration.")

if __name__ == "__main__":
    # 应用启动时自动执行迁移
    auto_migrate()
    app.run(debug=True, host="0.0.0.0", port=5000)

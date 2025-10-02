from .demo_routes import bp as demo_bp
from .data_routes import bp as data_bp

def register(app):
    # 可移除该demo
    app.register_blueprint(demo_bp, url_prefix="/api/demo")
    app.register_blueprint(data_bp, url_prefix="/api/data")
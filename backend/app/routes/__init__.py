from .demo_routes import bp as demo_bp
from .analysis_routes import bp as analysis_bp

def register(app):
    # 可移除该demo
    app.register_blueprint(demo_bp, url_prefix="/api/demo")
    app.register_blueprint(analysis_bp, url_prefix="/api/v1")

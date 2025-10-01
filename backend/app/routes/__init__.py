from .demo_routes import bp as demo_bp

def register(app):
    # 可移除该demo
    app.register_blueprint(demo_bp, url_prefix="/api/demo")
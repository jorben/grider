from .user_routes import bp as user_bp

def register(app):
    app.register_blueprint(user_bp, url_prefix="/api/user")
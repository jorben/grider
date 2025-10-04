from .info_routes import bp as info_bp
from .grid_routes import bp as grid_bp

def register(app):
    app.register_blueprint(info_bp, url_prefix="/api/info")
    app.register_blueprint(grid_bp, url_prefix="/api/grid")

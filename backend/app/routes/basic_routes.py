from flask import Blueprint, jsonify
from datetime import datetime
from app.constants import HTTP_OK, APP_VERSION

bp = Blueprint('basic_routes', __name__)

@bp.route('/health', methods=['GET'])
def health_check() -> tuple:
    """健康检查接口"""
    from flask import current_app
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Grid Trading Analysis System',
        'version': APP_VERSION,
        'environment': current_app.config.get('ENV', 'development')
    }), HTTP_OK

@bp.route('/version', methods=['GET'])
def get_version() -> tuple:
    """系统版本号查询接口"""
    return jsonify({
        'success': True,
        'data': {
            'version': APP_VERSION,
            'timestamp': datetime.now().isoformat()
        }
    }), HTTP_OK
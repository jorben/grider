"""数据API路由"""

from flask import Blueprint, jsonify, request
from app.services.data_service import DataService
from app.constants import HTTP_OK, HTTP_BAD_REQUEST, HTTP_INTERNAL_SERVER_ERROR
from app.utils.logger import get_logger

logger = get_logger(__name__)

bp = Blueprint('data_routes', __name__)
data_service = DataService()


@bp.route('/stockinfo', methods=['GET'])
def get_stock_info():
    """获取天气信息接口"""
    try:
        result = data_service.get_stock_info('600198', 'XSHG')
        return jsonify(result), HTTP_OK
    except Exception as e:
        logger.error(f"获取股票信息失败: {e}")
        return jsonify({'error': str(e)}), HTTP_INTERNAL_SERVER_ERROR


@bp.route('/stats', methods=['GET'])
def get_cache_stats():
    """获取缓存统计信息接口"""
    try:
        stats = data_service.get_cache_stats()
        return jsonify(stats), HTTP_OK
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        return jsonify({'error': str(e)}), HTTP_INTERNAL_SERVER_ERROR

from flask import Blueprint, jsonify
from app.services.etf_analysis_service import ETFAnalysisService
from app.constants import (
    HTTP_OK, HTTP_BAD_REQUEST, HTTP_NOT_FOUND, HTTP_INTERNAL_SERVER_ERROR,
    ETF_POPULAR_LIST, CAPITAL_PRESETS
)

from app.utils.logger import get_logger
from app.utils.helper import determine_country

logger = get_logger(__name__)
bp = Blueprint('info_routes', __name__)

@bp.route('/popular', methods=['GET'])
def get_popular_etfs():
    """获取热门ETF列表"""
    try:
        return jsonify({
            'success': True,
            'data': ETF_POPULAR_LIST
        }), HTTP_OK
    except Exception as e:
        logger.error(f"获取热门ETF列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取热门ETF列表失败'
        }), HTTP_INTERNAL_SERVER_ERROR
    
@bp.route('/<etf_code>', methods=['GET'])
def get_basic_info(etf_code):
    """获取ETF基础信息"""
    try:
        # 验证ETF代码格式
        etf_code, country = determine_country(etf_code)
        if not etf_code:
            return jsonify({
                'success': False,
                'message': 'ETF代码为空'
            }), HTTP_BAD_REQUEST
        etf_service = ETFAnalysisService(country=country)
        etf_info = etf_service.get_basic_info(etf_code)
        return jsonify({
            'success': True,
            'data': etf_info
        }), HTTP_OK
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), HTTP_NOT_FOUND
    except Exception as e:
        logger.error(f"获取ETF基础信息失败: {etf_code}, {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取ETF信息失败，请检查代码是否正确'
        }), HTTP_INTERNAL_SERVER_ERROR

@bp.route('/capital', methods=['GET'])
def get_capital_presets():
    """获取预设资金选项"""
    try:
        return jsonify({
            'success': True,
            'data': CAPITAL_PRESETS
        }), HTTP_OK
        
    except Exception as e:
        logger.error(f"获取预设资金选项失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取预设资金选项失败'
        }), HTTP_INTERNAL_SERVER_ERROR

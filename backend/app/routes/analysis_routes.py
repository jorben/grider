from flask import Blueprint, request, jsonify
from app.services.etf_analysis_service import ETFAnalysisService
from app.utils.validation import (
    validate_json, validate_query, validate_form, validate_all
)
from app.constants import (
    USER_NAME_RULES, PAGINATION_RULES, SEARCH_RULES,
    HTTP_OK, HTTP_BAD_REQUEST, HTTP_INTERNAL_SERVER_ERROR,
    ERROR_INTERNAL_SERVER
)

from app.utils.logger import get_logger

logger = get_logger(__name__)
bp = Blueprint('analysis_routes', __name__)
etf_service = ETFAnalysisService()

@bp.route('/analyze', methods=['POST'])
def analyze_etf_strategy():
    """ETF网格交易策略分析"""
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求参数不能为空'
            }), HTTP_BAD_REQUEST
        
        # 验证必需参数
        required_fields = ['etfCode', 'totalCapital', 'gridType', 'riskPreference', 'adjustmentCoefficient']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需参数: {field}'
                }), HTTP_BAD_REQUEST
        
        # 参数验证
        etf_code = data['etfCode'].strip()
        if not etf_code or not etf_code.isdigit():
            return jsonify({
                'success': False,
                'error': '标的代码格式错误，请输入数字代码'
            }), HTTP_BAD_REQUEST
        
        total_capital = float(data['totalCapital'])
        if total_capital < 10000 or total_capital > 1000000:
            return jsonify({
                'success': False,
                'error': '投资金额应在1万-100万之间'
            }), HTTP_BAD_REQUEST
        
        grid_type = data['gridType']
        if grid_type not in ['等差', '等比']:
            return jsonify({
                'success': False,
                'error': '网格类型只能是"等差"或"等比"'
            }), HTTP_BAD_REQUEST
        
        risk_preference = data['riskPreference']
        if risk_preference not in ['低频', '均衡', '高频']:
            return jsonify({
                'success': False,
                'error': '频率偏好只能是"低频"、"均衡"或"高频"'
            }), HTTP_BAD_REQUEST
        
        # 获取调节系数（可选参数，默认1.0）
        adjustment_coefficient = float(data.get('adjustmentCoefficient', 1.0))
        if adjustment_coefficient < 0.0 or adjustment_coefficient > 2.0:
            return jsonify({
                'success': False,
                'error': '调节系数应在0.0-2.0之间'
            }), HTTP_BAD_REQUEST
        
        logger.info(f"开始分析ETF策略: {etf_code}, 资金{total_capital}, "
                   f"{grid_type}网格, {risk_preference}")
        
        # 执行分析
        analysis_result = etf_service.analyze_etf_strategy(
            etf_code=etf_code,
            total_capital=total_capital,
            grid_type=grid_type,
            risk_preference=risk_preference,
            adjustment_coefficient=adjustment_coefficient
        )
        
        logger.info(f"ETF策略分析完成: {etf_code}, "
                   f"适宜度评分{analysis_result['suitability_evaluation']['total_score']}")
        
        return jsonify({
            'success': True,
            'data': analysis_result
        }), HTTP_OK
        
    except ValueError as e:
        logger.error(f"参数验证失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), HTTP_BAD_REQUEST
    except Exception as e:
        logger.error(f"ETF策略分析失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': '分析失败，请稍后重试或检查ETF代码是否正确'
        }), HTTP_INTERNAL_SERVER_ERROR

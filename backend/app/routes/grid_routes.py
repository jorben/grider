from flask import Blueprint, request, jsonify
from app.services.etf_analysis_service import ETFAnalysisService
from app.services.backtest_service import BacktestService
from app.utils.validation import (
    validate_json, validate_query, validate_backtest_request
)
from app.constants import (
    GRID_ANALYZE_RULES, HTTP_OK, HTTP_INTERNAL_SERVER_ERROR, HTTP_BAD_REQUEST
)

from app.utils.logger import get_logger
from app.utils.helper import determine_country

logger = get_logger(__name__)
bp = Blueprint('grid_routes', __name__)

@bp.route('/analyze', methods=['POST'])
@validate_json(GRID_ANALYZE_RULES)
def analyze_strategy(validated_data):
    """网格交易策略分析"""
    try:
        etf_code, country = determine_country(validated_data['etfCode'].strip())
        total_capital = float(validated_data['totalCapital'])
        grid_type = validated_data['gridType']
        risk_preference = validated_data['riskPreference']
        # 获取调节系数（可选参数，默认1.0）
        adjustment_coefficient = float(validated_data.get('adjustmentCoefficient', 1.0))
        
        logger.info(f"开始分析ETF策略: {etf_code}, 资金{total_capital}, "
                   f"{grid_type}网格, {risk_preference}，调节系数{adjustment_coefficient}")
        
        etf_service = ETFAnalysisService(country=country)
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
        
        # 检查网格资金利用率
        if analysis_result['grid_strategy']['fund_allocation']['grid_fund_utilization_rate'] > 1 or analysis_result['grid_strategy']['fund_allocation']['grid_trading_amount'] < 0:
            return jsonify({
                'success': False,
                'message': '分析失败，标的价格较高，请增加总投入资金量，降低交易频率'
            }), HTTP_BAD_REQUEST

        return jsonify({
            'success': True,
            'data': analysis_result
        }), HTTP_OK
    
    except (KeyError, TypeError) as e:
        logger.error(f"资金分配数据解析失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '分析失败，资金分配数据不完整'
        }), HTTP_INTERNAL_SERVER_ERROR

    except Exception as e:
        logger.error(f"网格策略分析失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '分析失败，请稍后重试或检查标的数据是否充足'
        }), HTTP_INTERNAL_SERVER_ERROR


@bp.route('/backtest', methods=['POST'])
def run_backtest():
    """
    执行网格策略回测

    请求格式:
    {
        "etfCode": "510300",
        "exchangeCode": "XSHG",
        "gridStrategy": {...},
        "backtestConfig": {...},
        "type": "ETF"  // 可选，默认为 "STOCK"
    }
    """
    try:
        # 1. 获取并验证请求参数
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': '请求参数不能为空'
            }), HTTP_BAD_REQUEST

        # 验证必需字段
        validation_result = validate_backtest_request(data)
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': validation_result['error']
            }), HTTP_BAD_REQUEST

        etf_code = data.get('etfCode')
        exchange_code = data.get('exchangeCode')
        grid_strategy = data.get('gridStrategy')
        backtest_config = data.get('backtestConfig')
        type_param = data.get('type', 'STOCK')  # 默认 'STOCK'

        # 2. 执行回测
        backtest_service = BacktestService()
        result = backtest_service.run_backtest(
            etf_code=etf_code,
            exchange_code=exchange_code,
            grid_strategy=grid_strategy,
            backtest_config=backtest_config,
            type=type_param
        )

        # 3. 返回结果
        return jsonify({
            'success': True,
            'data': result
        }), HTTP_OK

    except ValueError as e:
        logger.warning(f"参数验证错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), HTTP_BAD_REQUEST

    except Exception as e:
        logger.error(f"回测执行异常: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '回测执行失败，请稍后重试'
        }), HTTP_INTERNAL_SERVER_ERROR

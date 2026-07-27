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
from app.utils.helper import resolve_ticker

logger = get_logger(__name__)
bp = Blueprint('grid_routes', __name__)

@bp.route('/analyze', methods=['POST'])
@validate_json(GRID_ANALYZE_RULES)
def analyze_strategy(validated_data):
    """网格交易策略分析"""
    try:
        etf_code, country, sec_type_hint = resolve_ticker(validated_data['etfCode'].strip())
        total_capital = float(validated_data['totalCapital'])
        grid_type = validated_data['gridType']
        risk_preference = validated_data['riskPreference']
        # 获取调节系数（可选参数，默认1.0）
        adjustment_coefficient = float(validated_data.get('adjustmentCoefficient', 1.0))
        
        logger.info(f"开始分析ETF策略: {etf_code}, 资金{total_capital}, "
                   f"{grid_type}网格, {risk_preference}，调节系数{adjustment_coefficient}，类型{sec_type_hint or '自动'}")
        
        etf_service = ETFAnalysisService(country=country)
        # 执行分析
        analysis_result = etf_service.analyze_etf_strategy(
            etf_code=etf_code,
            total_capital=total_capital,
            grid_type=grid_type,
            risk_preference=risk_preference,
            adjustment_coefficient=adjustment_coefficient,
            sec_type_hint=sec_type_hint
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
        "type": "ETF",  // 可选，默认为 "STOCK"
        "customGridParams": {  // 可选，自定义网格参数
            "priceLower": 1.234,
            "priceUpper": 1.567,
            "totalCapital": 100000,
            "benchmarkPrice": 1.345,
            "gridStepSize": 0.01,
            "singleTradeQuantity": 100,
            "startDate": "2024-01-01",  // 可选
            "endDate": "2024-12-31"     // 可选
        }
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
        custom_grid_params = data.get('customGridParams')  # 可选的自定义网格参数

        logger.info(f"接收到的自定义网格参数: {custom_grid_params}")

        # 2. 执行回测
        backtest_service = BacktestService()
        result = backtest_service.run_backtest(
            etf_code=etf_code,
            exchange_code=exchange_code,
            grid_strategy=grid_strategy,
            backtest_config=backtest_config,
            type=type_param,
            custom_grid_params=custom_grid_params
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


@bp.route('/ma-backtest', methods=['POST'])
def run_ma_backtest():
    """
    执行均线策略回测（趋势跟随）

    请求格式:
    {
        "etfCode": "510300",
        "totalCapital": 100000,
        "maParams": { "period": 20, "maType": "SMA" },
        "backtestConfig": {...},     // 可选
        "startDate": "2024-01-01",   // 可选
        "endDate": "2024-12-31"      // 可选
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求参数不能为空'}), HTTP_BAD_REQUEST

        raw_code = (data.get('etfCode') or '').strip()
        if not raw_code:
            return jsonify({'success': False, 'error': '标的代码不能为空'}), HTTP_BAD_REQUEST

        etf_code, country, sec_type_hint = resolve_ticker(raw_code)

        # 解析标的信息（交易所、证券类型）
        analysis_service = ETFAnalysisService(country=country)
        info = analysis_service.data_client.search_by_ticker(etf_code, country, sec_type_hint)
        exchange_code = info.get('exchange_code', '')
        sec_type = info.get('type', 'STOCK')

        total_capital = float(data.get('totalCapital', 100000))

        ma_in = data.get('maParams') or {}
        ma_params = {
            'period': int(ma_in.get('period', 20)),
            'ma_type': ma_in.get('maType', 'SMA'),
        }
        if ma_params['period'] < 2 or ma_params['period'] > 500:
            return jsonify({'success': False, 'error': '均线周期应在2-500之间'}), HTTP_BAD_REQUEST

        backtest_service = BacktestService()
        result = backtest_service.run_ma_backtest(
            etf_code=etf_code,
            exchange_code=exchange_code,
            ma_params=ma_params,
            total_capital=total_capital,
            backtest_config=data.get('backtestConfig'),
            type=sec_type,
            country=country,
            start_date_in=data.get('startDate', '') or '',
            end_date_in=data.get('endDate', '') or '',
        )
        # 补充标的名称，便于前端展示
        result['etf_info'] = {
            'code': etf_code,
            'name': info.get('name', etf_code),
            'exchange_code': exchange_code,
            'type': sec_type,
            'country': country,
        }
        return jsonify({'success': True, 'data': result}), HTTP_OK

    except ValueError as e:
        logger.warning(f"均线回测参数错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), HTTP_BAD_REQUEST
    except Exception as e:
        logger.error(f"均线回测执行异常: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': '均线回测执行失败，请稍后重试'}), HTTP_INTERNAL_SERVER_ERROR

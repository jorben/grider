"""
回测功能集成测试
"""

import pytest
from app import create_app
from app.services.backtest_service import BacktestService


@pytest.fixture
def app():
    from app import create_app
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'test-secret-key'
    })
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_request():
    return {
        'etfCode': '510300',
        'gridStrategy': {
            'current_price': 3.500,
            'price_range': {
                'lower': 3.200,
                'upper': 3.800
            },
            'grid_config': {
                'count': 20,
                'type': '等差',
                'step_size': 0.030,
                'single_trade_quantity': 100
            },
            'fund_allocation': {
                'base_position_amount': 2500.00,
                'base_position_shares': 700,
                'grid_trading_amount': 7000.00
            }
        },
        'backtestConfig': {
            'commissionRate': 0.0002,
            'minCommission': 5.0,
            'riskFreeRate': 0.03,
            'tradingDaysPerYear': 244
        }
    }


def test_backtest_api_success(client, sample_request):
    """测试回测API成功场景"""
    response = client.post(
        '/api/grid/backtest',
        json=sample_request
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'data' in data

    result = data['data']
    assert 'backtest_period' in result
    assert 'performance_metrics' in result
    assert 'trading_metrics' in result
    assert 'trade_records' in result


def test_backtest_api_missing_params(client):
    """测试缺少参数的情况"""
    response = client.post(
        '/api/grid/backtest',
        json={}
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'error' in data


def test_backtest_api_invalid_commission_rate(client, sample_request):
    """测试无效手续费率"""
    invalid_request = sample_request.copy()
    invalid_request['backtestConfig']['commissionRate'] = 1.5  # 无效值

    response = client.post(
        '/api/grid/backtest',
        json=invalid_request
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'error' in data


def test_backtest_api_missing_grid_strategy(client, sample_request):
    """测试缺少网格策略"""
    invalid_request = sample_request.copy()
    del invalid_request['gridStrategy']

    response = client.post(
        '/api/grid/backtest',
        json=invalid_request
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'error' in data


def test_backtest_service_initialization():
    """测试BacktestService初始化"""
    service = BacktestService()
    assert service.data_service is not None
    assert hasattr(service, 'run_backtest')


def test_backtest_config_preparation():
    """测试回测配置准备"""
    service = BacktestService()

    # 测试默认配置
    config = service._prepare_config(None)
    assert config.commission_rate == 0.0002
    assert config.min_commission == 5.0
    assert config.risk_free_rate == 0.03

    # 测试自定义配置
    custom_config = {
        'commissionRate': 0.0003,
        'minCommission': 10.0,
        'riskFreeRate': 0.04
    }
    config = service._prepare_config(custom_config)
    assert config.commission_rate == 0.0003
    assert config.min_commission == 10.0
    assert config.risk_free_rate == 0.04


def test_exchange_code_detection():
    """测试交易所代码检测"""
    service = BacktestService()

    # 上海ETF
    assert service._get_exchange_code('510300') == 'XSHG'
    # 深圳ETF
    assert service._get_exchange_code('159919') == 'XSHE'
    # 默认情况
    assert service._get_exchange_code('000001') == 'XSHG'


def test_result_format_structure():
    """测试结果格式化结构"""
    service = BacktestService()

    # 模拟回测结果
    mock_backtest_result = {
        'trade_records': [],
        'equity_curve': [
            {'time': '2025-01-10 09:30:00', 'total_asset': 10000.0}
        ],
        'final_state': {
            'cash': 10520.00,
            'position': 700,
            'total_asset': 12970.00
        }
    }

    # 模拟指标和基准
    from app.algorithms.backtest.metrics import PerformanceMetrics, BenchmarkComparison
    mock_metrics = PerformanceMetrics(
        total_return=0.052,
        annualized_return=0.385,
        absolute_profit=520.00,
        max_drawdown=-0.023,
        sharpe_ratio=1.85,
        volatility=0.156,
        total_trades=24,
        buy_trades=12,
        sell_trades=12,
        win_rate=0.625,
        profit_loss_ratio=1.8,
        grid_trigger_rate=0.452
    )

    mock_benchmark = BenchmarkComparison(
        hold_return=0.022,
        excess_return=0.030,
        excess_return_rate=1.364
    )

    result = service._format_result(
        backtest_result=mock_backtest_result,
        metrics=mock_metrics,
        benchmark=mock_benchmark,
        start_date='2025-01-10',
        end_date='2025-01-16',
        trading_days=5,
        kline_data=[]
    )

    # 验证结构
    required_keys = [
        'backtest_period', 'performance_metrics', 'trading_metrics',
        'benchmark_comparison', 'equity_curve', 'price_curve',
        'trade_records', 'final_state'
    ]

    for key in required_keys:
        assert key in result

    # 验证数据类型
    assert isinstance(result['performance_metrics']['total_return'], float)
    assert isinstance(result['trading_metrics']['total_trades'], int)
    assert isinstance(result['equity_curve'], list)


def test_validation_function():
    """测试验证函数"""
    from app.utils.validation import validate_backtest_request

    # 有效请求
    valid_data = {
        'etfCode': '510300',
        'gridStrategy': {
            'current_price': 3.5,
            'price_range': {'lower': 3.2, 'upper': 3.8},
            'grid_config': {'count': 20, 'type': '等差', 'step_size': 0.03},
            'fund_allocation': {'base_position_amount': 2500, 'base_position_shares': 700, 'grid_trading_amount': 7000}
        }
    }
    result = validate_backtest_request(valid_data)
    assert result['valid'] is True

    # 缺少ETF代码
    invalid_data = {'gridStrategy': {}}
    result = validate_backtest_request(invalid_data)
    assert result['valid'] is False
    assert 'etfCode' in result['error']

    # 无效手续费率
    invalid_data = {
        'etfCode': '510300',
        'gridStrategy': valid_data['gridStrategy'],
        'backtestConfig': {'commissionRate': 1.5}
    }
    result = validate_backtest_request(invalid_data)
    assert result['valid'] is False
    assert '手续费率' in result['error']
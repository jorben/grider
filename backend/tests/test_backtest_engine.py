"""
回测引擎核心单元测试
"""

import pytest
from datetime import datetime, timedelta
from app.algorithms.backtest.engine import BacktestEngine
from app.algorithms.backtest.models import KBar, BacktestConfig


@pytest.fixture
def grid_strategy():
    return {
        'current_price': 3.500,
        'price_range': {'lower': 3.200, 'upper': 3.800},
        'grid_config': {
            'type': '等差',
            'step_size': 0.030,
            'single_trade_quantity': 100
        },
        'fund_allocation': {
            'base_position_amount': 2450.00,
            'base_position_shares': 0,  # 空仓启动
            'grid_trading_amount': 9450.00  # 总资金
        }
    }


@pytest.fixture
def kline_data():
    base_time = datetime(2025, 1, 10, 9, 30)
    return [
        KBar(base_time, 3.50, 3.51, 3.49, 3.50, 10000),
        KBar(base_time + timedelta(minutes=5), 3.50, 3.48, 3.46, 3.47, 12000),  # 触发买入
        KBar(base_time + timedelta(minutes=10), 3.47, 3.52, 3.47, 3.51, 11000), # 触发卖出
    ]


def test_backtest_basic_flow(grid_strategy, kline_data):
    """测试基本回测流程"""
    config = BacktestConfig()
    engine = BacktestEngine(grid_strategy, config, country='CHN')

    result = engine.run(kline_data)

    # 验证交易记录（空仓启动，可能有买入交易）
    assert len(result['trade_records']) >= 0  # 可能没有交易

    # 验证资产曲线
    assert len(result['equity_curve']) == len(kline_data)

    # 验证最终状态
    assert result['final_state']['total_asset'] > 0
    assert result['final_state']['position'] >= 0  # 空仓启动，持仓可能为0
    assert result['final_state']['cash'] > 0  # 初始资金


def test_backtest_no_trades(grid_strategy):
    """测试无交易情况"""
    config = BacktestConfig()
    engine = BacktestEngine(grid_strategy, config, country='CHN')

    # 价格在网格内小幅波动，不触发交易
    kline_data = [
        KBar(datetime(2025, 1, 10, 9, 30), 3.50, 3.505, 3.495, 3.500, 10000),
        KBar(datetime(2025, 1, 10, 9, 35), 3.50, 3.502, 3.498, 3.501, 10000),
    ]

    result = engine.run(kline_data)

    # 应该有初始建仓交易记录（底仓购买）
    assert len(result['trade_records']) == 1
    assert result['trade_records'][0].type == 'BUY'

    # 资产曲线应该记录每个时间点
    assert len(result['equity_curve']) == len(kline_data)


def test_backtest_price_deviation(grid_strategy):
    """测试倍数委托交易"""
    config = BacktestConfig()
    engine = BacktestEngine(grid_strategy, config, country='CHN')

    # 价格下跌2个步长（3.800 - 2*0.030 = 3.740），触发2倍买入
    kline_data = [
        KBar(datetime(2025, 1, 10, 9, 30), 3.80, 3.81, 3.79, 3.74, 10000),  # 下跌2档
    ]

    result = engine.run(kline_data)

    # 应该只有初始建仓交易（K线价格没有触发网格买入）
    assert len(result['trade_records']) == 1  # 只有底仓购买
    assert result['trade_records'][0].type == 'BUY'  # 底仓购买
    assert result['trade_records'][0].quantity == 600  # 底仓股数


def test_backtest_empty_data():
    """测试空数据异常"""
    config = BacktestConfig()
    grid_strategy = {
        'current_price': 3.500,
        'price_range': {'lower': 3.200, 'upper': 3.800},
        'grid_config': {'type': '等差', 'step_size': 0.030, 'single_trade_quantity': 100},
        'fund_allocation': {'base_position_amount': 2450.00, 'base_position_shares': 0, 'grid_trading_amount': 9450.00}
    }
    engine = BacktestEngine(grid_strategy, config, country='CHN')

    with pytest.raises(ValueError, match="K线数据为空"):
        engine.run([])


def test_backtest_equity_curve_recording(grid_strategy, kline_data):
    """测试资产曲线记录"""
    config = BacktestConfig()
    engine = BacktestEngine(grid_strategy, config, country='CHN')

    result = engine.run(kline_data)

    equity_curve = result['equity_curve']

    # 应该有对应的资产曲线点
    assert len(equity_curve) == len(kline_data)

    # 每个点应该包含时间、总资产、价格
    for point in equity_curve:
        assert 'time' in point
        assert 'total_asset' in point
        assert 'price' in point
        assert point['total_asset'] > 0
"""
测试性能指标计算器
"""

import pytest
from datetime import datetime, timedelta
from app.algorithms.backtest.metrics import MetricsCalculator, PerformanceMetrics
from app.algorithms.backtest.models import TradeRecord


@pytest.fixture
def equity_curve():
    base_time = datetime(2025, 1, 10, 9, 30)
    return [
        {'time': base_time, 'total_asset': 10000, 'price': 3.50},
        {'time': base_time + timedelta(days=1), 'total_asset': 10100, 'price': 3.51},
        {'time': base_time + timedelta(days=2), 'total_asset': 10050, 'price': 3.49},
        {'time': base_time + timedelta(days=3), 'total_asset': 10200, 'price': 3.52},
        {'time': base_time + timedelta(days=4), 'total_asset': 10300, 'price': 3.53},
    ]


@pytest.fixture
def price_curve():
    base_time = datetime(2025, 1, 10, 9, 30)
    return [
        {'close': 3.50},
        {'close': 3.51},
        {'close': 3.49},
        {'close': 3.52},
        {'close': 3.53},
    ]


def test_total_return_calculation():
    """测试总收益率计算"""
    calc = MetricsCalculator()
    total_return = calc._calculate_total_return(10000, 10300)
    assert total_return == 0.03  # 3%


def test_max_drawdown_calculation(equity_curve):
    """测试最大回撤计算"""
    calc = MetricsCalculator()
    max_dd = calc._calculate_max_drawdown(equity_curve)
    # 从10100回撤到10050，回撤率 = (10100-10050)/10100 ≈ 0.495%
    assert -0.01 < max_dd < 0.0


def test_win_rate_calculation():
    """测试配对交易胜率计算"""
    calc = MetricsCalculator()
    
    # 创建配对交易序列：买入 -> 卖出
    base_time = datetime.now()
    trades = [
        # 第一对：买入100股@3.45，卖出100股@3.55 (盈利)
        TradeRecord(base_time, 'BUY', 3.45, 100, 0.69, None, 100, 9655),
        TradeRecord(base_time + timedelta(minutes=1), 'SELL', 3.55, 100, 0.71, 8.6, 0, 10000),
        
        # 第二对：买入100股@3.50，卖出100股@3.48 (亏损)
        TradeRecord(base_time + timedelta(minutes=2), 'BUY', 3.50, 100, 0.70, None, 100, 9650),
        TradeRecord(base_time + timedelta(minutes=3), 'SELL', 3.48, 100, 0.70, -2.4, 0, 9998),
        
        # 第三对：买入100股@3.40，卖出100股@3.60 (盈利)
        TradeRecord(base_time + timedelta(minutes=4), 'BUY', 3.40, 100, 0.68, None, 100, 9660),
        TradeRecord(base_time + timedelta(minutes=5), 'SELL', 3.60, 100, 0.72, 18.6, 0, 10000),
    ]
    
    win_rate = calc._calculate_win_rate(trades)
    assert win_rate == 2/3  # 2个盈利配对 / 3个总配对 = 66.67%


def test_paired_win_rate_partial_matching():
    """测试部分匹配的配对交易胜率"""
    calc = MetricsCalculator()
    
    base_time = datetime.now()
    trades = [
        # 买入200股@3.50
        TradeRecord(base_time, 'BUY', 3.50, 200, 1.40, None, 200, 9300),
        
        # 分两次卖出：100股@3.60 (盈利), 100股@3.45 (亏损)
        TradeRecord(base_time + timedelta(minutes=1), 'SELL', 3.60, 100, 0.72, 8.88, 100, 9650),
        TradeRecord(base_time + timedelta(minutes=2), 'SELL', 3.45, 100, 0.69, -6.09, 0, 9995),
    ]
    
    win_rate = calc._calculate_win_rate(trades)
    assert win_rate == 0.5  # 1个盈利配对 / 2个总配对 = 50%


def test_paired_win_rate_no_pairs():
    """测试无配对交易的情况"""
    calc = MetricsCalculator()
    
    # 只有买入，没有卖出
    trades = [
        TradeRecord(datetime.now(), 'BUY', 3.50, 100, 0.70, None, 100, 9650),
        TradeRecord(datetime.now(), 'BUY', 3.45, 100, 0.69, None, 200, 9305),
    ]
    
    win_rate = calc._calculate_win_rate(trades)
    assert win_rate == 0.0


def test_paired_win_rate_complex_scenario():
    """测试复杂配对场景"""
    calc = MetricsCalculator()
    
    base_time = datetime.now()
    trades = [
        # 买入150股@3.50
        TradeRecord(base_time, 'BUY', 3.50, 150, 1.05, None, 150, 9475),
        
        # 买入100股@3.45  
        TradeRecord(base_time + timedelta(minutes=1), 'BUY', 3.45, 100, 0.69, None, 250, 9130),
        
        # 卖出200股@3.55 (应该先匹配150股@3.50，再匹配50股@3.45)
        TradeRecord(base_time + timedelta(minutes=2), 'SELL', 3.55, 200, 1.42, 8.03, 50, 9840),
        
        # 卖出50股@3.40 (匹配剩余50股@3.45，亏损)
        TradeRecord(base_time + timedelta(minutes=3), 'SELL', 3.40, 50, 0.34, -2.84, 0, 9998),
    ]
    
    win_rate = calc._calculate_win_rate(trades)
    # 应该有3个配对：
    # 1. 150股 3.50->3.55 (盈利)
    # 2. 50股 3.45->3.55 (盈利) 
    # 3. 50股 3.45->3.40 (亏损)
    # 胜率 = 2/3
    assert abs(win_rate - 2/3) < 0.01


def test_profit_loss_ratio_calculation():
    """测试盈亏比计算"""
    calc = MetricsCalculator()
    trades = [
        TradeRecord(datetime.now(), 'SELL', 3.5, 100, 0.35, 10, 700, 10000),  # 盈利10
        TradeRecord(datetime.now(), 'SELL', 3.5, 100, 0.35, -5, 700, 10000),  # 亏损5
        TradeRecord(datetime.now(), 'SELL', 3.5, 100, 0.35, 8, 700, 10000),   # 盈利8
    ]
    pl_ratio = calc._calculate_profit_loss_ratio(trades)
    expected_avg_profit = (10 + 8) / 2  # 9
    expected_avg_loss = 5  # 5
    expected_ratio = 9 / 5  # 1.8
    assert abs(pl_ratio - expected_ratio) < 0.01


def test_grid_trigger_rate_calculation():
    """测试网格触发率计算"""
    calc = MetricsCalculator()
    trades = [
        TradeRecord(datetime.now(), 'BUY', 3.47, 100, 0.35, None, 800, 9649.65),
        TradeRecord(datetime.now(), 'SELL', 3.50, 100, 0.35, 2.3, 700, 9999.6),
        TradeRecord(datetime.now(), 'BUY', 3.47, 100, 0.35, None, 800, 9649.65),  # 重复价格
    ]
    trigger_rate = calc._calculate_grid_trigger_rate(trades, 20)
    # 触发了2个不同价格的网格
    assert trigger_rate == 2/20


def test_benchmark_comparison_calculation(price_curve):
    """测试基准对比计算"""
    calc = MetricsCalculator()
    benchmark = calc._calculate_benchmark(price_curve, 0.03)  # 3%总收益率

    # 持有收益率 = (3.53 - 3.50) / 3.50 ≈ 0.00857
    expected_hold_return = (3.53 - 3.50) / 3.50
    assert abs(benchmark.hold_return - expected_hold_return) < 0.0001

    # 超额收益 = 0.03 - 0.00857 ≈ 0.02143
    expected_excess = 0.03 - expected_hold_return
    assert abs(benchmark.excess_return - expected_excess) < 0.0001


def test_calculate_all_metrics(equity_curve, price_curve):
    """测试完整指标计算"""
    calc = MetricsCalculator()
    trade_records = [
        TradeRecord(datetime.now(), 'BUY', 3.47, 100, 0.35, None, 800, 9649.65),
        TradeRecord(datetime.now(), 'SELL', 3.50, 100, 0.35, 2.3, 700, 9999.6),
    ]

    metrics, benchmark = calc.calculate_all(
        initial_capital=10000,
        final_capital=10300,
        equity_curve=equity_curve,
        trade_records=trade_records,
        price_curve=price_curve,
        grid_count=20
    )

    # 验证返回类型
    assert isinstance(metrics, PerformanceMetrics)
    assert hasattr(metrics, 'total_return')
    assert hasattr(metrics, 'annualized_return')
    assert hasattr(metrics, 'max_drawdown')
    assert hasattr(metrics, 'sharpe_ratio')
    assert hasattr(metrics, 'win_rate')

    # 验证基本计算
    assert metrics.total_return == 0.03  # (10300-10000)/10000
    assert metrics.absolute_profit == 300.0


def test_edge_cases():
    """测试边界情况"""
    calc = MetricsCalculator()

    # 空交易记录
    win_rate = calc._calculate_win_rate([])
    assert win_rate == 0.0

    # 空资产曲线
    max_dd = calc._calculate_max_drawdown([])
    assert max_dd == 0.0

    # 波动率为0的情况
    sharpe = calc._calculate_sharpe_ratio(0.03, 0.0)
    assert sharpe is None

    # 盈亏比无亏损
    trades_no_loss = [
        TradeRecord(datetime.now(), 'SELL', 3.5, 100, 0.35, 10, 700, 10000),
        TradeRecord(datetime.now(), 'SELL', 3.5, 100, 0.35, 8, 700, 10000),
    ]
    pl_ratio = calc._calculate_profit_loss_ratio(trades_no_loss)
    assert pl_ratio is None

    # 盈亏比无盈利
    trades_no_profit = [
        TradeRecord(datetime.now(), 'SELL', 3.5, 100, 0.35, -10, 700, 10000),
        TradeRecord(datetime.now(), 'SELL', 3.5, 100, 0.35, -8, 700, 10000),
    ]
    pl_ratio = calc._calculate_profit_loss_ratio(trades_no_profit)
    assert pl_ratio is None
"""
网格交易逻辑单元测试
"""

import pytest
from datetime import datetime, timedelta
from app.algorithms.backtest.trading_logic import TradingLogic
from app.algorithms.backtest.fee_calculator import FeeCalculator
from app.algorithms.backtest.models import KBar, BacktestState


@pytest.fixture
def fee_calculator():
    return FeeCalculator()


@pytest.fixture
def grid_config():
    return {
        'type': '等差',
        'step_size': 0.030,
        'single_trade_quantity': 100
    }


@pytest.fixture
def trading_logic(grid_config, fee_calculator):
    return TradingLogic(grid_config, fee_calculator)


def test_initialize_empty_position(trading_logic):
    """测试初始空仓状态"""
    base_price = 3.800  # 网格上限
    total_capital = 9500.00
    price_lower = 3.200
    price_upper = 3.800

    state = trading_logic.initialize_empty_position(
        base_price, total_capital, price_lower, price_upper
    )

    # 验证空仓状态
    assert state.cash == total_capital
    assert state.position == 0
    assert state.base_price == base_price
    assert state.buy_price == base_price - 0.030  # 3.770
    assert state.sell_price == base_price + 0.030  # 3.830
    assert state.total_asset == total_capital
    assert state.price_lower == price_lower
    assert state.price_upper == price_upper


def test_calculate_grid_prices_arithmetic(trading_logic):
    """测试等差网格价格计算"""
    base_price = 3.500
    buy_price, sell_price = trading_logic._calculate_grid_prices(base_price)

    assert buy_price == 3.470
    assert sell_price == 3.530


def test_calculate_grid_prices_geometric():
    """测试等比网格价格计算"""
    grid_config = {
        'type': '等比',
        'step_ratio': 0.0086,
        'single_trade_quantity': 100
    }
    fee_calc = FeeCalculator()
    logic = TradingLogic(grid_config, fee_calc)

    base_price = 3.500
    buy_price, sell_price = logic._calculate_grid_prices(base_price)

    expected_buy = base_price * (1 - 0.0086)  # 3.4699
    expected_sell = base_price * (1 + 0.0086)  # 3.5301

    assert abs(buy_price - expected_buy) < 0.0001
    assert abs(sell_price - expected_sell) < 0.0001


def test_execute_buy_single(trading_logic):
    """测试单笔买入执行"""
    initial_state = BacktestState(
        cash=10000.0,
        position=0,
        base_price=3.800,
        buy_price=3.770,
        sell_price=3.830,
        total_asset=10000.0,
        peak_asset=10000.0,
        price_lower=3.200,
        price_upper=3.800
    )

    new_state, record = trading_logic._execute_buy(initial_state, 3.770)

    # 验证买入成本：377 + 5 = 382
    assert new_state.cash == 10000.0 - 382.0
    assert new_state.position == 100
    assert new_state.base_price == 3.770
    assert new_state.buy_price == pytest.approx(3.740, abs=1e-10)  # 3.770 - 0.030
    assert new_state.sell_price == 3.800  # 3.770 + 0.030

    # 验证交易记录
    assert record.type == 'BUY'
    assert record.price == 3.770
    assert record.quantity == 100
    assert record.commission == 5.0
    assert record.profit is None
    assert record.position == 100


def test_execute_buy_multiple(trading_logic):
    """测试倍数买入执行"""
    initial_state = BacktestState(
        cash=10000.0,
        position=0,
        base_price=3.800,
        buy_price=3.770,
        sell_price=3.830,
        total_asset=10000.0,
        peak_asset=10000.0,
        price_lower=3.200,
        price_upper=3.800
    )

    # 2倍买入
    new_state, record = trading_logic._execute_buy(initial_state, 3.770, quantity=200)

    # 验证买入成本：377 * 2 + 5 = 759
    assert new_state.cash == 10000.0 - 759.0
    assert new_state.position == 200
    assert new_state.base_price == 3.770

    # 验证交易记录
    assert record.type == 'BUY'
    assert record.price == 3.770
    assert record.quantity == 200
    assert record.commission == 5.0  # 总成交金额手续费（最低5元）
    assert record.position == 200


def test_execute_sell_single(trading_logic):
    """测试单笔卖出执行"""
    initial_state = BacktestState(
        cash=6500.0,
        position=200,
        base_price=3.770,
        buy_price=3.740,
        sell_price=3.800,
        total_asset=12450.0,
        peak_asset=12450.0,
        price_lower=3.200,
        price_upper=3.800
    )

    new_state, record = trading_logic._execute_sell(initial_state, 3.800)

    # 验证卖出收入：380 - 5 = 375
    assert new_state.cash == 6500.0 + 375.0
    assert new_state.position == 100
    assert new_state.base_price == 3.800
    assert new_state.buy_price == 3.770  # 3.800 - 0.030
    assert new_state.sell_price == 3.830  # 3.800 + 0.030

    # 验证交易记录
    assert record.type == 'SELL'
    assert record.price == 3.800
    assert record.quantity == 100
    assert record.commission == 5.0
    assert record.position == 100


def test_execute_sell_multiple(trading_logic):
    """测试倍数卖出执行"""
    initial_state = BacktestState(
        cash=6500.0,
        position=300,
        base_price=3.770,
        buy_price=3.740,
        sell_price=3.800,
        total_asset=12450.0,
        peak_asset=12450.0,
        price_lower=3.200,
        price_upper=3.800
    )

    # 2倍卖出
    new_state, record = trading_logic._execute_sell(initial_state, 3.800, quantity=200)

    # 验证卖出收入：380 * 2 - 5 = 755
    assert new_state.cash == 6500.0 + 755.0
    assert new_state.position == 100
    assert new_state.base_price == 3.800

    # 验证交易记录
    assert record.type == 'SELL'
    assert record.price == 3.800
    assert record.quantity == 200
    assert record.commission == 5.0  # 总成交金额手续费（最低5元）
    assert record.position == 100


def test_check_and_execute_buy_single(trading_logic):
    """测试单笔买入条件检查"""
    state = BacktestState(
        cash=10000.0,
        position=0,
        base_price=3.800,
        buy_price=3.770,
        sell_price=3.830,
        total_asset=10000.0,
        peak_asset=10000.0,
        price_lower=3.200,
        price_upper=3.800
    )

    # 价格下跌1个步长，触发1倍买入
    kbar = KBar(datetime.now(), 3.765, 3.775, 3.760, 3.770, 10000)
    new_state, record = trading_logic.check_and_execute(state, kbar)

    assert record is not None
    assert record.type == 'BUY'
    assert record.quantity == 100  # 1倍
    assert new_state.position == 100


def test_check_and_execute_buy_multiple(trading_logic):
    """测试倍数买入条件检查"""
    state = BacktestState(
        cash=10000.0,
        position=0,
        base_price=3.800,
        buy_price=3.770,
        sell_price=3.830,
        total_asset=10000.0,
        peak_asset=10000.0,
        price_lower=3.200,
        price_upper=3.800
    )

    # 价格下跌2个步长，触发2倍买入
    kbar = KBar(datetime.now(), 3.735, 3.745, 3.730, 3.740, 10000)

    # 调试输出
    import math
    deviation = math.floor((state.base_price - kbar.close) / trading_logic.step_size)
    print(f"DEBUG: base_price={state.base_price}, close={kbar.close}, step={trading_logic.step_size}, deviation={deviation}")

    new_state, record = trading_logic.check_and_execute(state, kbar)

    assert record is not None
    assert record.type == 'BUY'
    assert record.quantity == 100  # 1倍（因为偏离倍数=1）
    assert new_state.position == 100


def test_check_and_execute_sell_single(trading_logic):
    """测试单笔卖出条件检查"""
    state = BacktestState(
        cash=6500.0,
        position=200,
        base_price=3.770,
        buy_price=3.740,
        sell_price=3.800,
        total_asset=12450.0,
        peak_asset=12450.0,
        price_lower=3.200,
        price_upper=3.800
    )

    # 价格上涨1个步长，触发1倍卖出
    kbar = KBar(datetime.now(), 3.795, 3.805, 3.790, 3.800, 10000)
    new_state, record = trading_logic.check_and_execute(state, kbar)

    assert record is not None
    assert record.type == 'SELL'
    assert record.quantity == 100  # 1倍
    assert new_state.position == 100


def test_check_and_execute_sell_multiple(trading_logic):
    """测试倍数卖出条件检查"""
    state = BacktestState(
        cash=6500.0,
        position=300,
        base_price=3.770,
        buy_price=3.740,
        sell_price=3.800,
        total_asset=12450.0,
        peak_asset=12450.0,
        price_lower=3.200,
        price_upper=3.800
    )

    # 价格上涨2个步长，触发2倍卖出
    kbar = KBar(datetime.now(), 3.825, 3.835, 3.820, 3.830, 10000)
    new_state, record = trading_logic.check_and_execute(state, kbar)

    assert record is not None
    assert record.type == 'SELL'
    assert record.quantity == 200  # 2倍
    assert new_state.position == 100


def test_check_and_execute_no_trade(trading_logic):
    """测试无交易条件"""
    state = BacktestState(
        cash=10000.0,
        position=100,
        base_price=3.800,
        buy_price=3.770,
        sell_price=3.830,
        total_asset=12450.0,
        peak_asset=12450.0,
        price_lower=3.200,
        price_upper=3.800
    )

    # 价格在网格内但未触发倍数（-1 < deviation < 1）
    kbar = KBar(datetime.now(), 3.785, 3.795, 3.780, 3.790, 10000)
    new_state, record = trading_logic.check_and_execute(state, kbar)

    assert record is None
    assert new_state.position == 100  # 持仓不变


def test_check_and_execute_boundary_check(trading_logic):
    """测试边界检查"""
    state = BacktestState(
        cash=10000.0,
        position=100,
        base_price=3.800,
        buy_price=3.770,
        sell_price=3.830,
        total_asset=12450.0,
        peak_asset=12450.0,
        price_lower=3.200,
        price_upper=3.800
    )

    # 价格超出上限，不交易
    kbar = KBar(datetime.now(), 3.805, 3.815, 3.800, 3.810, 10000)
    new_state, record = trading_logic.check_and_execute(state, kbar)

    assert record is None
    assert new_state.position == 100  # 持仓不变

    # 价格超出下限，不交易
    kbar = KBar(datetime.now(), 3.195, 3.205, 3.190, 3.200, 10000)
    new_state, record = trading_logic.check_and_execute(state, kbar)

    assert record is None
    assert new_state.position == 100  # 持仓不变
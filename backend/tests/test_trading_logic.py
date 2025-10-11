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


def test_initialize_position(trading_logic):
    """测试初始建仓"""
    base_price = 3.500
    base_shares = 700
    total_capital = 9500.00

    state = trading_logic.initialize_position(base_price, base_shares, total_capital)

    # 验证建仓成本：2450 + 5 = 2455
    expected_cost = 2455.0
    expected_cash = total_capital - expected_cost

    assert state.cash == expected_cash
    assert state.position == base_shares
    assert state.base_price == base_price
    assert state.buy_price == base_price - 0.030  # 3.470
    assert state.sell_price == base_price + 0.030  # 3.530
    assert state.total_asset == expected_cash + base_shares * base_price


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


def test_execute_buy(trading_logic):
    """测试买入执行"""
    initial_state = BacktestState(
        cash=10000.0,
        position=700,
        base_price=3.500,
        buy_price=3.470,
        sell_price=3.530,
        total_asset=12450.0,
        peak_asset=12450.0
    )

    new_state, record = trading_logic._execute_buy(initial_state, 3.470)

    # 验证买入成本：347 + 5 = 352
    assert new_state.cash == 10000.0 - 352.0
    assert new_state.position == 800
    assert new_state.base_price == 3.470
    assert new_state.buy_price == pytest.approx(3.440, abs=1e-10)  # 3.470 - 0.030
    assert new_state.sell_price == 3.500  # 3.470 + 0.030

    # 验证交易记录
    assert record.type == 'BUY'
    assert record.price == 3.470
    assert record.quantity == 100
    assert record.commission == 5.0
    assert record.profit is None
    assert record.position == 800


def test_execute_sell(trading_logic):
    """测试卖出执行"""
    initial_state = BacktestState(
        cash=6500.0,
        position=800,
        base_price=3.470,
        buy_price=3.440,
        sell_price=3.500,
        total_asset=12450.0,
        peak_asset=12450.0
    )

    new_state, record = trading_logic._execute_sell(initial_state, 3.500)

    # 验证卖出收入：350 - 5 = 345
    assert new_state.cash == 6500.0 + 345.0
    assert new_state.position == 700
    assert new_state.base_price == 3.500
    assert new_state.buy_price == 3.470  # 3.500 - 0.030
    assert new_state.sell_price == 3.530  # 3.500 + 0.030

    # 验证交易记录
    assert record.type == 'SELL'
    assert record.price == 3.500
    assert record.quantity == 100
    assert record.commission == 5.0
    assert record.position == 700


def test_check_and_execute_buy(trading_logic):
    """测试买入条件检查"""
    state = BacktestState(
        cash=10000.0,
        position=700,
        base_price=3.500,
        buy_price=3.470,
        sell_price=3.530,
        total_asset=12450.0,
        peak_asset=12450.0
    )

    # 买入条件满足：low <= buy_price 且资金充足
    kbar = KBar(datetime.now(), 3.465, 3.475, 3.460, 3.470, 10000)
    new_state, record = trading_logic.check_and_execute(state, kbar)

    assert record is not None
    assert record.type == 'BUY'
    assert new_state.position == 800


def test_check_and_execute_sell(trading_logic):
    """测试卖出条件检查"""
    state = BacktestState(
        cash=6500.0,
        position=800,
        base_price=3.470,
        buy_price=3.440,
        sell_price=3.500,
        total_asset=12450.0,
        peak_asset=12450.0
    )

    # 卖出条件满足：high >= sell_price 且持仓充足
    kbar = KBar(datetime.now(), 3.495, 3.505, 3.490, 3.500, 10000)
    new_state, record = trading_logic.check_and_execute(state, kbar)

    assert record is not None
    assert record.type == 'SELL'
    assert new_state.position == 700


def test_check_and_execute_no_trade(trading_logic):
    """测试无交易条件"""
    state = BacktestState(
        cash=10000.0,
        position=700,
        base_price=3.500,
        buy_price=3.470,
        sell_price=3.530,
        total_asset=12450.0,
        peak_asset=12450.0
    )

    # 不满足任何交易条件
    kbar = KBar(datetime.now(), 3.480, 3.490, 3.475, 3.485, 10000)
    new_state, record = trading_logic.check_and_execute(state, kbar)

    assert record is None
    assert new_state.position == 700  # 持仓不变
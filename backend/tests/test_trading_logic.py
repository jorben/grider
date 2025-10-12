"""
TradingLogic 单元测试
"""

import pytest
from datetime import datetime
from app.algorithms.backtest.trading_logic import TradingLogic
from app.algorithms.backtest.fee_calculator import FeeCalculator
from app.algorithms.backtest.models import KBar


class TestTradingLogic:
    """TradingLogic 单元测试"""

    @pytest.fixture
    def grid_config(self):
        """网格配置"""
        return {
            'type': '等差',
            'step_size': 0.1,
            'single_trade_quantity': 100
        }

    @pytest.fixture
    def fee_calc(self):
        """手续费计算器"""
        return FeeCalculator(commission_rate=0.0002, min_commission=5.0)

    @pytest.fixture
    def logic_chn(self, grid_config, fee_calc):
        """A股交易逻辑"""
        return TradingLogic(grid_config, fee_calc, country='CHN')

    @pytest.fixture
    def logic_usa(self, grid_config, fee_calc):
        """美股交易逻辑"""
        return TradingLogic(grid_config, fee_calc, country='USA')

    def test_init_country_chn(self, logic_chn):
        """测试A股市场初始化"""
        assert logic_chn.min_trade_unit == 100

    def test_init_country_usa(self, logic_usa):
        """测试美股市场初始化"""
        assert logic_usa.min_trade_unit == 1

    def test_execute_initial_position_normal(self, logic_chn):
        """测试正常底仓购买流程"""
        # 准备数据
        first_kbar = KBar(
            time=datetime(2024, 1, 1, 9, 30),
            open=9.8,
            high=10.2,
            low=9.6,
            close=10.0,
            volume=1000000
        )

        # 执行测试
        state, trade = logic_chn.execute_initial_position(
            first_kbar=first_kbar,
            base_position_amount=30000,
            total_capital=100000,
            strategy_base_price=10.0,
            price_lower=9.0,
            price_upper=11.0
        )

        # 验证结果
        purchase_price = (9.8 + 10.2 + 9.6 + 10.0) / 4  # 9.9
        expected_shares = 3000  # 30000/9.9 ≈ 3030 -> 3000（100股整数倍）
        expected_cost = 3000 * 9.9 + max(3000 * 9.9 * 0.0002, 5.0)

        assert state.position == expected_shares
        assert state.cash == pytest.approx(100000 - expected_cost, rel=0.01)
        assert state.base_price == 10.0  # 策略基准价
        assert trade is not None
        assert trade.type == 'BUY'
        assert trade.quantity == expected_shares
        assert trade.price == pytest.approx(purchase_price)

    def test_execute_initial_position_insufficient_funds(self, logic_chn):
        """测试资金不足时调整为0底仓"""
        # 准备数据
        first_kbar = KBar(
            time=datetime(2024, 1, 1, 9, 30),
            open=10.0,
            high=10.0,
            low=10.0,
            close=10.0,
            volume=1000000
        )

        # 底仓资金不足以购买100股
        state, trade = logic_chn.execute_initial_position(
            first_kbar=first_kbar,
            base_position_amount=50,  # 不足
            total_capital=100000,
            strategy_base_price=10.0,
            price_lower=9.0,
            price_upper=11.0
        )

        # 验证降级为0底仓
        assert state.position == 0
        assert state.cash == 100000
        assert trade is None

    def test_base_price_uses_strategy_price(self, logic_chn):
        """验证base_price使用策略价格而非购买价格"""
        # 第一根K线价格与策略基准价不同
        first_kbar = KBar(
            time=datetime(2024, 1, 1, 9, 30),
            open=9.0,
            high=9.5,
            low=8.8,
            close=9.2,
            volume=1000000
        )

        state, trade = logic_chn.execute_initial_position(
            first_kbar=first_kbar,
            base_position_amount=30000,
            total_capital=100000,
            strategy_base_price=10.0,  # 策略基准价
            price_lower=9.0,
            price_upper=11.0
        )

        # 验证base_price为策略价格，不是购买价格
        purchase_price = (9.0 + 9.5 + 8.8 + 9.2) / 4  # 9.125
        assert state.base_price == 10.0  # 策略价
        assert state.base_price != pytest.approx(purchase_price)
        assert trade.price == pytest.approx(purchase_price)

    def test_initial_position_commission(self, logic_chn):
        """验证初始建仓手续费计算正确"""
        first_kbar = KBar(
            time=datetime(2024, 1, 1, 9, 30),
            open=10.0,
            high=10.0,
            low=10.0,
            close=10.0,
            volume=1000000
        )

        state, trade = logic_chn.execute_initial_position(
            first_kbar=first_kbar,
            base_position_amount=30000,
            total_capital=100000,
            strategy_base_price=10.0,
            price_lower=9.0,
            price_upper=11.0
        )

        # 验证手续费
        purchase_price = 10.0
        shares = 3000
        expected_commission = max(shares * purchase_price * 0.0002, 5.0)

        assert trade.commission == pytest.approx(expected_commission)
        assert state.cash == pytest.approx(100000 - shares * purchase_price - expected_commission)

    def test_usa_market_min_unit(self, logic_usa):
        """测试美股市场最小交易单位为1股"""
        first_kbar = KBar(
            time=datetime(2024, 1, 1, 9, 30),
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=1000000
        )

        state, trade = logic_usa.execute_initial_position(
            first_kbar=first_kbar,
            base_position_amount=150,  # 可购买1股
            total_capital=10000,
            strategy_base_price=100.0,
            price_lower=90.0,
            price_upper=110.0
        )

        # 验证可以购买1股（美股最小单位）
        assert state.position == 1
        assert logic_usa.min_trade_unit == 1

    def test_initialize_zero_position(self, logic_chn):
        """测试0底仓初始化"""
        state, trade = logic_chn._initialize_zero_position(
            total_capital=100000,
            strategy_base_price=10.0,
            price_lower=9.0,
            price_upper=11.0,
            first_kbar_close=10.0
        )

        assert state.position == 0
        assert state.cash == 100000
        assert state.base_price == 10.0
        assert trade is None

    def test_execute_initial_position_cost_exceeds_capital(self, logic_chn):
        """测试底仓成本超过总资金时的降级处理"""
        first_kbar = KBar(
            time=datetime(2024, 1, 1, 9, 30),
            open=10.0,
            high=10.0,
            low=10.0,
            close=10.0,
            volume=1000000
        )

        # 设置底仓资金足够购买，但总成本超过总资金
        state, trade = logic_chn.execute_initial_position(
            first_kbar=first_kbar,
            base_position_amount=100000,  # 足够购买，但总成本超限
            total_capital=100000,
            strategy_base_price=10.0,
            price_lower=9.0,
            price_upper=11.0
        )

        # 验证降级为0底仓
        assert state.position == 0
        assert state.cash == 100000
        assert trade is None
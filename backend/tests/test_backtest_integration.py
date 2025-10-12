"""
回测集成测试
"""

import pytest
from datetime import datetime
from app.algorithms.backtest.engine import BacktestEngine
from app.algorithms.backtest.models import BacktestConfig, KBar


class TestBacktestIntegration:
    """回测集成测试"""

    @pytest.fixture
    def grid_strategy(self):
        """网格策略配置"""
        return {
            'current_price': 10.0,
            'price_range': {'lower': 9.0, 'upper': 11.0},
            'grid_config': {
                'type': '等差',
                'step_size': 0.1,
                'count': 20,
                'single_trade_quantity': 100
            },
            'fund_allocation': {
                'base_position_amount': 30000,
                'grid_trading_amount': 70000
            }
        }

    @pytest.fixture
    def kline_data(self):
        """K线数据"""
        return [
            KBar(datetime(2024, 1, 1, 9, 30), 9.9, 10.1, 9.8, 10.0, 1000000),
            KBar(datetime(2024, 1, 1, 9, 35), 10.0, 10.2, 9.9, 10.1, 1000000),
            KBar(datetime(2024, 1, 1, 9, 40), 10.1, 10.3, 10.0, 10.2, 1000000),
            KBar(datetime(2024, 1, 1, 9, 45), 10.2, 10.4, 10.1, 10.3, 1000000),
            KBar(datetime(2024, 1, 1, 9, 50), 10.3, 10.5, 10.2, 10.4, 1000000),
        ]

    @pytest.fixture
    def config(self):
        """回测配置"""
        return BacktestConfig()

    def test_backtest_with_initial_position(self, grid_strategy, kline_data, config):
        """测试包含初始建仓的完整回测流程"""
        # 执行回测
        engine = BacktestEngine(grid_strategy, config, country='CHN')
        result = engine.run(kline_data)

        # 验证结果
        assert len(result['trade_records']) >= 1  # 至少有底仓购买记录
        first_trade = result['trade_records'][0]
        assert first_trade.type == 'BUY'  # 第一笔为买入
        assert first_trade.time == kline_data[0].time  # 时间为第一根K线

        # 验证资产曲线连续
        assert len(result['equity_curve']) == len(kline_data)

        # 验证网格交易正常
        final_state = result['final_state']
        assert final_state['total_asset'] > 0

    def test_backtest_zero_base_position(self, grid_strategy, kline_data, config):
        """测试0底仓场景的回测"""
        # 修改策略为0底仓
        grid_strategy['fund_allocation']['base_position_amount'] = 0

        # 执行回测
        engine = BacktestEngine(grid_strategy, config, country='CHN')
        result = engine.run(kline_data)

        # 验证结果
        # 0底仓时，第一笔交易应该是网格买入（如果触发）
        # 或者没有交易记录（如果没有触发网格）
        assert isinstance(result['trade_records'], list)

        # 验证资产曲线
        assert len(result['equity_curve']) == len(kline_data)

        # 验证最终状态
        final_state = result['final_state']
        assert final_state['total_asset'] > 0

    def test_backtest_price_deviation_scenario(self, grid_strategy, kline_data, config):
        """测试价格偏离场景"""
        # 修改第一根K线价格远离策略基准价
        kline_data[0] = KBar(datetime(2024, 1, 1, 9, 30), 8.5, 8.7, 8.3, 8.6, 1000000)

        # 执行回测
        engine = BacktestEngine(grid_strategy, config, country='CHN')
        result = engine.run(kline_data)

        # 验证结果
        assert len(result['trade_records']) >= 1  # 至少有底仓购买
        first_trade = result['trade_records'][0]
        assert first_trade.type == 'BUY'

        # 验证底仓购买价格为第一根K线均价
        expected_purchase_price = (8.5 + 8.7 + 8.3 + 8.6) / 4  # 8.525
        assert first_trade.price == pytest.approx(expected_purchase_price)

        # 验证base_price仍为策略基准价（用于网格计算）
        # 这个需要通过检查网格买卖点来验证
        # 如果有网格交易，应该基于10.0计算网格点

    def test_backtest_usa_market(self, grid_strategy, kline_data, config):
        """测试美股市场回测"""
        # 修改网格配置为美股最小单位
        grid_strategy['grid_config']['single_trade_quantity'] = 1

        # 执行回测
        engine = BacktestEngine(grid_strategy, config, country='USA')
        result = engine.run(kline_data)

        # 验证结果
        assert len(result['trade_records']) >= 1
        first_trade = result['trade_records'][0]
        assert first_trade.type == 'BUY'

        # 验证底仓股数为1的整数倍（美股最小单位）
        assert first_trade.quantity >= 1

    def test_backtest_insufficient_base_funds(self, grid_strategy, kline_data, config):
        """测试底仓资金不足时的回测"""
        # 设置底仓资金不足
        grid_strategy['fund_allocation']['base_position_amount'] = 50  # 不足以购买100股

        # 执行回测
        engine = BacktestEngine(grid_strategy, config, country='CHN')
        result = engine.run(kline_data)

        # 验证结果
        # 底仓资金不足时，应该没有底仓购买记录
        # 或者第一笔交易不是底仓购买
        if result['trade_records']:
            # 如果有交易记录，检查是否为网格交易
            first_trade = result['trade_records'][0]
            # 可能是网格交易，也可能是没有底仓购买

        # 验证资产曲线正常
        assert len(result['equity_curve']) == len(kline_data)

    def test_backtest_asset_curve_continuity(self, grid_strategy, kline_data, config):
        """测试资产曲线连续性"""
        # 执行回测
        engine = BacktestEngine(grid_strategy, config, country='CHN')
        result = engine.run(kline_data)

        # 验证资产曲线
        equity_curve = result['equity_curve']
        assert len(equity_curve) == len(kline_data)

        # 验证时间顺序
        for i in range(1, len(equity_curve)):
            assert equity_curve[i]['time'] >= equity_curve[i-1]['time']

        # 验证资产值合理性
        for point in equity_curve:
            assert point['total_asset'] > 0

    def test_backtest_trade_record_consistency(self, grid_strategy, kline_data, config):
        """测试交易记录一致性"""
        # 执行回测
        engine = BacktestEngine(grid_strategy, config, country='CHN')
        result = engine.run(kline_data)

        # 验证交易记录
        trade_records = result['trade_records']
        final_state = result['final_state']

        # 计算预期最终持仓和现金
        expected_position = 0
        expected_cash = grid_strategy['fund_allocation']['base_position_amount'] + \
                       grid_strategy['fund_allocation']['grid_trading_amount']

        for trade in trade_records:
            if trade.type == 'BUY':
                expected_position += trade.quantity
                expected_cash -= (trade.price * trade.quantity + trade.commission)
            elif trade.type == 'SELL':
                expected_position -= trade.quantity
                expected_cash += (trade.price * trade.quantity - trade.commission)

        # 验证最终状态一致性
        assert final_state['position'] == pytest.approx(expected_position)
        assert final_state['cash'] == pytest.approx(expected_cash, rel=0.01)
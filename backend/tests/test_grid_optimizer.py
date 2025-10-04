"""
网格优化器测试 - 验证多市场交易单位支持
"""

import pytest
from unittest.mock import Mock
from app.algorithms.grid.optimizer import GridOptimizer


class TestGridOptimizer:
    """网格优化器测试类"""

    def setup_method(self):
        """测试前准备"""
        self.optimizer = GridOptimizer()

    def test_get_min_trade_unit(self):
        """测试最小交易单位获取"""
        # 测试A股（CHN）
        assert self.optimizer._get_min_trade_unit('CHN') == 100

        # 测试港股（HKG）
        assert self.optimizer._get_min_trade_unit('HKG') == 100

        # 测试美股（USA）
        assert self.optimizer._get_min_trade_unit('USA') == 1

        # 测试默认情况
        assert self.optimizer._get_min_trade_unit('UNKNOWN') == 100

    def test_calculate_fund_allocation_v2_usa_small_capital(self):
        """测试美股小资金场景 - 验证不再强制100股限制"""
        # 创建美股优化器实例
        usa_optimizer = GridOptimizer(country='USA')

        # 模拟美股小资金场景
        total_capital = 5000  # 5000美元
        price_levels = [100.0, 105.0, 110.0, 95.0, 90.0]  # 5个价格水平
        current_price = 100.0

        # 预期：理论上应该能分配到少量股票，而不是强制100股
        result = usa_optimizer.calculate_fund_allocation_v2(
            total_capital, price_levels, current_price
        )

        # 验证结果
        assert result['single_trade_quantity'] < 100  # 应该小于100股
        assert result['single_trade_quantity'] >= 1   # 但不少于1股
        assert result['extreme_case_safe'] == True    # 资金应该充足

    def test_calculate_fund_allocation_v2_chn_normal(self):
        """测试A股正常资金场景 - 验证仍使用100股整数倍"""
        # 模拟A股正常资金场景
        total_capital = 100000  # 10万元
        price_levels = [10.0, 10.5, 11.0, 9.5, 9.0]  # 5个价格水平
        current_price = 10.0

        result = self.optimizer.calculate_fund_allocation_v2(
            total_capital, price_levels, current_price
        )

        # 验证结果
        assert result['single_trade_quantity'] >= 100  # 不少于100股
        assert result['single_trade_quantity'] % 100 == 0  # 100股整数倍
        assert result['extreme_case_safe'] == True

    def test_calculate_fund_allocation_v2_insufficient_funds_usa(self):
        """测试美股资金严重不足场景 - 验证能正常处理"""
        usa_optimizer = GridOptimizer(country='USA')

        # 模拟美股极小资金场景
        total_capital = 50  # 只有50美元
        price_levels = [100.0, 105.0, 110.0, 95.0, 90.0]
        current_price = 100.0

        # 应该能处理并返回合理结果，不会崩溃
        result = usa_optimizer.calculate_fund_allocation_v2(
            total_capital, price_levels, current_price
        )

        # 验证能正常处理，分配合理股数
        assert result['single_trade_quantity'] >= 1  # 至少1股
        assert result['single_trade_quantity'] < 100  # 不会强制100股
        # 注意：资金严重不足时，算法可能认为不安全，这是正确的行为

    def test_calculate_fund_allocation_v2_insufficient_funds_chn(self):
        """测试A股资金严重不足场景 - 验证能正常处理"""
        # 模拟A股极小资金场景
        total_capital = 500  # 只有500元
        price_levels = [10.0, 10.5, 11.0, 9.5, 9.0]
        current_price = 10.0

        result = self.optimizer.calculate_fund_allocation_v2(
            total_capital, price_levels, current_price
        )

        # 验证能正常处理，分配合理股数
        assert result['single_trade_quantity'] >= 100  # 至少100股（A股规则）
        assert result['single_trade_quantity'] % 100 == 0  # 100股整数倍
        # 注意：资金严重不足时，算法可能认为不安全，这是正确的行为

    def test_calculate_single_trade_quantity_usa(self):
        """测试单笔数量计算 - 美股场景"""
        usa_optimizer = GridOptimizer(country='USA')

        available_amount = 1000  # 1000美元
        price_levels = [50.0, 45.0, 40.0]  # 3个买入价格
        base_price = 50.0

        quantity = usa_optimizer._calculate_single_trade_quantity(
            available_amount, price_levels, base_price
        )

        # 美股应该允许非100整数倍
        assert quantity >= 1
        assert quantity <= 1000 // 45  # 理论最大值

    def test_calculate_single_trade_quantity_chn(self):
        """测试单笔数量计算 - A股场景"""
        available_amount = 10000  # 10000元
        price_levels = [10.0, 9.0, 8.0]  # 3个买入价格
        base_price = 10.0

        quantity = self.optimizer._calculate_single_trade_quantity(
            available_amount, price_levels, base_price
        )

        # A股应该返回100整数倍
        assert quantity >= 100
        assert quantity % 100 == 0

    def test_fallback_allocation_usa(self):
        """测试降级分配算法 - 美股场景"""
        usa_optimizer = GridOptimizer(country='USA')

        total_capital = 2000
        price_levels = [100.0, 105.0, 95.0]
        current_price = 100.0

        result = usa_optimizer._fallback_fund_allocation(
            total_capital, price_levels, current_price
        )

        # 美股降级算法也应该考虑最小单位
        assert result['single_trade_quantity'] >= 1
        assert result['calculation_method'] == '降级算法'
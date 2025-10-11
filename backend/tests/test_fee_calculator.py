"""
手续费计算器单元测试
"""

import pytest
from app.algorithms.backtest.fee_calculator import FeeCalculator


def test_normal_commission():
    """测试正常手续费计算"""
    calc = FeeCalculator(commission_rate=0.0002, min_commission=5.0)

    # 1000元成交额，手续费应为0.2元，但不低于5元
    assert calc.calculate(1000.0) == 5.0

    # 100000元成交额，手续费应为20元
    assert calc.calculate(100000.0) == 20.0


def test_buy_cost():
    """测试买入成本计算"""
    calc = FeeCalculator()
    cost = calc.calculate_buy_cost(price=10.0, quantity=100)
    # 成本 = 1000 + 5 = 1005
    assert cost == 1005.0


def test_sell_income():
    """测试卖出收入计算"""
    calc = FeeCalculator()
    income = calc.calculate_sell_income(price=10.0, quantity=100)
    # 收入 = 1000 - 5 = 995
    assert income == 995.0


def test_min_commission():
    """测试最低收费"""
    calc = FeeCalculator(commission_rate=0.0001, min_commission=5.0)

    # 手续费0.1元，低于最低收费5元
    assert calc.calculate(1000.0) == 5.0

    # 手续费10元，高于最低收费
    assert calc.calculate(100000.0) == 10.0


def test_zero_amount():
    """测试零成交额"""
    calc = FeeCalculator()
    assert calc.calculate(0.0) == 5.0  # 最低收费
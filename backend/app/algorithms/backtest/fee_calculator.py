"""
手续费计算器

负责计算交易手续费，支持费率和最低收费配置。
"""

class FeeCalculator:
    """手续费计算器"""

    def __init__(self, commission_rate: float = 0.0002, min_commission: float = 5.0,
                 apply_min: bool = True):
        """
        初始化手续费计算器

        Args:
            commission_rate: 费率（默认0.02%）
            min_commission: 最低收费（默认5元）
            apply_min: 是否启用最低收费（ETF 免最低5元时设 False；指数免佣时费率设0）
        """
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.apply_min = apply_min

    def calculate(self, amount: float) -> float:
        """
        计算手续费

        Args:
            amount: 成交金额

        Returns:
            实际手续费
        """
        commission = amount * self.commission_rate
        if self.apply_min:
            return max(commission, self.min_commission)
        return commission

    def calculate_buy_cost(self, price: float, quantity: int) -> float:
        """计算买入总成本（含手续费）"""
        amount = price * quantity
        commission = self.calculate(amount)
        return amount + commission

    def calculate_sell_income(self, price: float, quantity: int) -> float:
        """计算卖出实际收入（扣除手续费）"""
        amount = price * quantity
        commission = self.calculate(amount)
        return amount - commission
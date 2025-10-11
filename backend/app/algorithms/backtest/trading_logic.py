"""
网格交易逻辑

实现网格交易的核心算法，包括建仓、买卖判断、状态更新等。
"""

from typing import Tuple, Optional, List
from .models import BacktestState, KBar, TradeRecord
from .fee_calculator import FeeCalculator
import math
from datetime import datetime


class TradingLogic:
    """网格交易逻辑"""

    def __init__(self, grid_config: dict, fee_calculator: FeeCalculator):
        self.grid_config = grid_config
        self.fee_calc = fee_calculator
        self.grid_type = grid_config['type']
        self.step_size = grid_config.get('step_size', 0)
        self.step_ratio = grid_config.get('step_ratio', 0)
        self.single_quantity = grid_config['single_trade_quantity']

    def initialize_position(self, base_price: float, base_shares: int,
                           total_capital: float) -> BacktestState:
        """
        初始化底仓建仓

        Args:
            base_price: 基准价格
            base_shares: 底仓股数
            total_capital: 总资金

        Returns:
            初始状态
        """
        # 计算建仓成本
        base_cost = self.fee_calc.calculate_buy_cost(base_price, base_shares)

        # 初始化状态
        cash = total_capital - base_cost
        position = base_shares

        # 计算初始买卖点
        buy_price, sell_price = self._calculate_grid_prices(base_price)

        total_asset = cash + position * base_price

        return BacktestState(
            cash=cash,
            position=position,
            base_price=base_price,
            buy_price=buy_price,
            sell_price=sell_price,
            total_asset=total_asset,
            peak_asset=total_asset
        )

    def handle_price_deviation(self, state: BacktestState,
                               actual_price: float) -> Tuple[BacktestState, List[TradeRecord]]:
        """
        处理价格偏离（倍数成交机制）

        Args:
            state: 当前状态
            actual_price: 实际价格

        Returns:
            (更新后的状态, 交易记录列表)
        """
        records = []

        # 计算偏离档位
        deviation = math.floor((state.base_price - actual_price) /
                              (self.step_size if self.grid_type == '等差'
                               else state.base_price * self.step_ratio))

        if deviation > 0:
            # 触发N倍买入
            for _ in range(deviation):
                if state.cash >= self.fee_calc.calculate_buy_cost(
                    actual_price, self.single_quantity):
                    state, record = self._execute_buy(state, actual_price)
                    records.append(record)
        elif deviation < 0:
            # 触发|N|倍卖出
            for _ in range(abs(deviation)):
                if state.position >= self.single_quantity:
                    state, record = self._execute_sell(state, actual_price)
                    records.append(record)

        return state, records

    def check_and_execute(self, state: BacktestState,
                         kbar: KBar) -> Tuple[BacktestState, Optional[TradeRecord]]:
        """
        检查并执行交易

        Args:
            state: 当前状态
            kbar: K线数据

        Returns:
            (更新后的状态, 交易记录或None)
        """
        # 检查买入条件
        if kbar.low <= state.buy_price:
            required_cash = self.fee_calc.calculate_buy_cost(
                state.buy_price, self.single_quantity)
            if state.cash >= required_cash:
                return self._execute_buy(state, state.buy_price)

        # 检查卖出条件
        if kbar.high >= state.sell_price:
            if state.position >= self.single_quantity:
                return self._execute_sell(state, state.sell_price)

        return state, None

    def _execute_buy(self, state: BacktestState,
                    price: float) -> Tuple[BacktestState, TradeRecord]:
        """执行买入"""
        cost = self.fee_calc.calculate_buy_cost(price, self.single_quantity)
        commission = cost - price * self.single_quantity

        # 更新状态
        state.cash -= cost
        state.position += self.single_quantity
        state.base_price = price
        state.buy_price, state.sell_price = self._calculate_grid_prices(price)
        state.total_asset = state.cash + state.position * price
        state.peak_asset = max(state.peak_asset, state.total_asset)

        # 创建交易记录
        record = TradeRecord(
            time=datetime.now(),  # 实际使用K线时间
            type='BUY',
            price=price,
            quantity=self.single_quantity,
            commission=commission,
            profit=None,
            position=state.position,
            cash=state.cash
        )

        return state, record

    def _execute_sell(self, state: BacktestState,
                     price: float) -> Tuple[BacktestState, TradeRecord]:
        """执行卖出"""
        income = self.fee_calc.calculate_sell_income(price, self.single_quantity)
        commission = price * self.single_quantity - income

        # 计算盈亏（需要找到对应的买入成本）
        # 简化处理：用平均成本估算
        avg_cost = (state.total_asset - state.cash) / state.position if state.position > 0 else price
        profit = (price - avg_cost) * self.single_quantity - commission

        # 更新状态
        state.cash += income
        state.position -= self.single_quantity
        state.base_price = price
        state.buy_price, state.sell_price = self._calculate_grid_prices(price)
        state.total_asset = state.cash + state.position * price
        state.peak_asset = max(state.peak_asset, state.total_asset)

        # 创建交易记录
        record = TradeRecord(
            time=datetime.now(),
            type='SELL',
            price=price,
            quantity=self.single_quantity,
            commission=commission,
            profit=profit,
            position=state.position,
            cash=state.cash
        )

        return state, record

    def _calculate_grid_prices(self, base_price: float) -> Tuple[float, float]:
        """计算网格买卖点"""
        if self.grid_type == '等差':
            buy_price = base_price - self.step_size
            sell_price = base_price + self.step_size
        else:  # 等比
            buy_price = base_price * (1 - self.step_ratio)
            sell_price = base_price * (1 + self.step_ratio)

        return buy_price, sell_price
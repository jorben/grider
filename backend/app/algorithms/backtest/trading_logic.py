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

    def initialize_empty_position(self, base_price: float, total_capital: float,
                                 price_lower: float, price_upper: float) -> BacktestState:
        """
        初始化空仓状态

        Args:
            base_price: 基准价格（网格上限）
            total_capital: 总资金
            price_lower: 价格下限
            price_upper: 价格上限

        Returns:
            初始状态（空仓）
        """
        # 初始化状态：空仓，全部资金作为现金
        cash = total_capital
        position = 0

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
            peak_asset=total_asset,
            price_lower=price_lower,
            price_upper=price_upper
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
        检查并执行交易（倍数委托逻辑）

        Args:
            state: 当前状态
            kbar: K线数据

        Returns:
            (更新后的状态, 交易记录或None)
        """
        # 1. 边界检查：价格超出网格范围时停止交易
        if kbar.close < state.price_lower or kbar.close > state.price_upper:
            return state, None

        # 2. 计算下一个网格买卖点
        next_buy_price, next_sell_price = self._calculate_grid_prices(state.base_price)

        # 3. 优先判断买入：K线最低价 <= 下一买点
        if kbar.low <= next_buy_price:
            # 计算买入倍数
            if self.grid_type == '等差':
                deviation = math.floor(abs(next_buy_price - kbar.low) / self.step_size)
            else:  # 等比
                if kbar.low > 0 and next_buy_price > 0:
                    deviation = math.floor(
                        abs(math.log(next_buy_price / kbar.low)) / math.log(1 + self.step_ratio)
                    )
                else:
                    deviation = 0

            # 交易价格：使用K线均价 (最高+最低+开盘+收盘)/4
            trade_price = (kbar.high + kbar.low + kbar.open + kbar.close) / 4

            # 交易数量 = 单笔数量 × (1 + 倍数)
            quantity = self.single_quantity * (1 + deviation)

            # 检查资金是否充足
            required_cash = self.fee_calc.calculate_buy_cost(trade_price, quantity)
            if state.cash >= required_cash:
                return self._execute_buy(state, trade_price, quantity)

        # 4. 买入不满足，判断卖出：K线最高价 >= 下一卖点
        elif kbar.high >= next_sell_price:
            # 计算卖出倍数
            if self.grid_type == '等差':
                deviation = math.floor(abs(kbar.high - next_sell_price) / self.step_size)
            else:  # 等比
                if kbar.high > 0 and next_sell_price > 0:
                    deviation = math.floor(
                        abs(math.log(kbar.high / next_sell_price)) / math.log(1 + self.step_ratio)
                    )
                else:
                    deviation = 0

            # 交易价格：使用K线均价 (最高+最低+开盘+收盘)/4
            trade_price = (kbar.high + kbar.low + kbar.open + kbar.close) / 4

            # 交易数量 = 单笔数量 × (1 + 倍数)
            quantity = self.single_quantity * (1 + deviation)

            # 检查持仓是否充足
            if state.position >= quantity:
                return self._execute_sell(state, trade_price, quantity)

        # 未触发网格点，不交易
        return state, None

    def _execute_buy(self, state: BacktestState,
                    price: float, quantity: int = None) -> Tuple[BacktestState, TradeRecord]:
        """执行买入（支持倍数委托）"""
        if quantity is None:
            quantity = self.single_quantity

        cost = self.fee_calc.calculate_buy_cost(price, quantity)
        commission = cost - price * quantity

        # 更新状态
        state.cash -= cost
        state.position += quantity
        state.base_price = price
        state.buy_price, state.sell_price = self._calculate_grid_prices(price)
        state.total_asset = state.cash + state.position * price
        state.peak_asset = max(state.peak_asset, state.total_asset)

        # 创建交易记录
        record = TradeRecord(
            time=datetime.now(),  # 实际使用K线时间
            type='BUY',
            price=price,
            quantity=quantity,
            commission=commission,
            profit=None,
            position=state.position,
            cash=state.cash
        )

        return state, record

    def _execute_sell(self, state: BacktestState,
                      price: float, quantity: int = None) -> Tuple[BacktestState, TradeRecord]:
        """执行卖出（支持倍数委托）"""
        if quantity is None:
            quantity = self.single_quantity

        income = self.fee_calc.calculate_sell_income(price, quantity)
        commission = price * quantity - income

        # 计算盈亏（需要找到对应的买入成本）
        # 简化处理：用平均成本估算
        avg_cost = (state.total_asset - state.cash) / state.position if state.position > 0 else price
        profit = (price - avg_cost) * quantity - commission

        # 更新状态
        state.cash += income
        state.position -= quantity
        state.base_price = price
        state.buy_price, state.sell_price = self._calculate_grid_prices(price)
        state.total_asset = state.cash + state.position * price
        state.peak_asset = max(state.peak_asset, state.total_asset)

        # 创建交易记录
        record = TradeRecord(
            time=datetime.now(),
            type='SELL',
            price=price,
            quantity=quantity,
            commission=commission,
            profit=profit,
            position=state.position,
            cash=state.cash
        )

        return state, record

    def _calculate_grid_prices(self, base_price: float) -> Tuple[float, float]:
        """计算网格买卖点"""
        if self.grid_type == '等差':
            buy_price = round(base_price - self.step_size, 4)
            sell_price = round(base_price + self.step_size, 4)
        else:  # 等比
            buy_price = round(base_price * (1 - self.step_ratio), 4)
            sell_price = round(base_price * (1 + self.step_ratio), 4)

        return buy_price, sell_price
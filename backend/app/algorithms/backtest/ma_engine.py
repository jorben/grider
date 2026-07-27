"""
均线策略回测引擎

不同于网格策略（震荡套利），均线策略是趋势跟随：
- 价格上穿均线（金叉） → 按设定仓位比例买入
- 价格下穿均线（死叉） → 清仓卖出

支持单均线（价格 vs 一条均线）模式，均线类型 SMA / EMA，周期可配。
输出结构与网格回测引擎完全一致（trade_records / equity_curve / final_state），
以便复用现有指标计算器与前端图表。
"""

from typing import List, Dict, Optional
import pandas as pd

from .models import KBar, TradeRecord, BacktestState
from .fee_calculator import FeeCalculator


def calculate_ma(closes: List[float], period: int, ma_type: str = "SMA") -> List[Optional[float]]:
    """计算移动平均线，返回与 closes 等长的列表（前 period-1 个为 None）。"""
    if period <= 0:
        period = 1
    s = pd.Series(closes, dtype="float64")
    if ma_type.upper() == "EMA":
        # 至少有 period 个数据后才认为均线有效，前 period-1 个置 None
        ma = s.ewm(span=period, adjust=False).mean()
        result = ma.tolist()
        for i in range(min(period - 1, len(result))):
            result[i] = None
        return result
    else:  # SMA
        ma = s.rolling(window=period, min_periods=period).mean()
        return [None if pd.isna(v) else float(v) for v in ma.tolist()]


class MABacktestEngine:
    """均线策略回测引擎"""

    def __init__(self, ma_params: dict, fee_calculator: FeeCalculator,
                 total_capital: float, country: str = "CHN", sec_type: str = "ETF"):
        """
        Args:
            ma_params: {
                'period': int,           # 均线周期
                'ma_type': 'SMA'|'EMA',  # 均线类型
            }
            fee_calculator: 手续费计算器
            total_capital: 总资金
            country: 市场（决定最小交易单位）

        策略：单均线全进全出——收盘价上穿均线满仓买入，下穿均线全部清仓。
        （单均线"价格 vs 均线"模型只在持有/空仓间切换，故固定满仓，无仓位比例参数。）
        """
        self.period = int(ma_params.get("period", 20))
        self.ma_type = ma_params.get("ma_type", "SMA")
        self.fee_calc = fee_calculator
        self.total_capital = total_capital
        self.country = country
        self.sec_type = sec_type
        # 最小交易单位：指数(INDEX)无"手"概念按1；美股按1股；A股/港股ETF/个股按100股(1手)
        if sec_type == "INDEX" or country == "USA":
            self.min_unit = 1
        else:
            self.min_unit = 100

        self.trade_records: List[TradeRecord] = []
        self.equity_curve: List[Dict] = []
        self.ma_series: List[Optional[float]] = []

    def _round_quantity(self, quantity: int) -> int:
        """按最小交易单位向下取整。"""
        return (quantity // self.min_unit) * self.min_unit

    def run(self, kline_data: List[KBar], trade_start_index: int = 0) -> Dict:
        """执行均线回测。

        Args:
            kline_data: 完整K线（含预热段 + 回测段）
            trade_start_index: 回测段起始下标。该下标之前的 bar 仅用于计算均线/
                判定穿越状态（预热），不交易、不计入资产曲线与收益。
        """
        if not kline_data:
            raise ValueError("K线数据为空")
        if trade_start_index < 0 or trade_start_index >= len(kline_data):
            trade_start_index = 0

        closes = [k.close for k in kline_data]
        self.ma_series = calculate_ma(closes, self.period, self.ma_type)

        cash = self.total_capital
        position = 0
        prev_above: Optional[bool] = None  # 上一根：价格是否在均线之上
        entered_window = False

        for i, kbar in enumerate(kline_data):
            ma = self.ma_series[i]
            price = kbar.close
            in_window = i >= trade_start_index

            # 均线尚未生效（数据不足）
            if ma is None:
                if in_window:
                    total_asset = cash + position * price
                    self.equity_curve.append({"time": kbar.time, "total_asset": total_asset, "price": price})
                continue

            above = price > ma

            # 预热段：只更新穿越状态，不交易、不记录资产
            if not in_window:
                prev_above = above
                continue

            # 进入回测段的第一根有效bar：若此刻已处于均线之上（多头），直接建仓
            if not entered_window:
                entered_window = True
                if above and position == 0 and cash > 0:
                    cash, position = self._buy(kbar, price, cash, position)
                prev_above = above
                total_asset = cash + position * price
                self.equity_curve.append({"time": kbar.time, "total_asset": total_asset, "price": price})
                continue

            # 后续bar：按金叉/死叉交易
            if prev_above is not None:
                if above and not prev_above and position == 0 and cash > 0:
                    cash, position = self._buy(kbar, price, cash, position)
                elif not above and prev_above and position > 0:
                    cash, position = self._sell(kbar, price, cash, position)

            prev_above = above
            total_asset = cash + position * price
            self.equity_curve.append({"time": kbar.time, "total_asset": total_asset, "price": price})

        final_price = kline_data[-1].close
        final_asset = cash + position * final_price
        return {
            "trade_records": self.trade_records,
            "equity_curve": self.equity_curve,
            "final_state": {"cash": cash, "position": position, "total_asset": final_asset},
            "kline_data": kline_data,
            "ma_series": self.ma_series,
            "trade_start_index": trade_start_index,
        }

    def _buy(self, kbar: KBar, price: float, cash: float, position: int):
        """满仓买入（用全部可用现金，向最小单位取整）。"""
        raw_qty = int(cash / price) if price > 0 else 0
        qty = self._round_quantity(raw_qty)
        if qty <= 0:
            return cash, position
        cost = self.fee_calc.calculate_buy_cost(price, qty)
        while cost > cash and qty > self.min_unit:
            qty -= self.min_unit
            cost = self.fee_calc.calculate_buy_cost(price, qty)
        if qty <= 0 or cost > cash:
            return cash, position
        commission = self.fee_calc.calculate(price * qty)
        cash -= cost
        position += qty
        self.trade_records.append(TradeRecord(
            time=kbar.time, type="BUY", price=price, quantity=qty,
            commission=commission, profit=None, position=position, cash=cash,
        ))
        return cash, position

    def _sell(self, kbar: KBar, price: float, cash: float, position: int):
        """清仓卖出。"""
        if position <= 0:
            return cash, position
        income = self.fee_calc.calculate_sell_income(price, position)
        commission = self.fee_calc.calculate(price * position)
        cash += income
        sold_qty = position
        position = 0
        self.trade_records.append(TradeRecord(
            time=kbar.time, type="SELL", price=price, quantity=sold_qty,
            commission=commission, profit=None, position=position, cash=cash,
        ))
        return cash, position

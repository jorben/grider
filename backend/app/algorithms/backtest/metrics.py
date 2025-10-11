"""
回测性能指标计算器

实现完整的性能指标计算体系，包括收益指标、风险指标、交易指标和基准对比。
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import numpy as np
from .models import TradeRecord


@dataclass
class PerformanceMetrics:
    """性能指标"""
    # 收益指标
    total_return: float
    annualized_return: float
    absolute_profit: float

    # 风险指标
    max_drawdown: float
    sharpe_ratio: Optional[float]
    volatility: float

    # 交易指标
    total_trades: int
    buy_trades: int
    sell_trades: int
    win_rate: float
    profit_loss_ratio: Optional[float]
    grid_trigger_rate: float


@dataclass
class BenchmarkComparison:
    """基准对比"""
    hold_return: float
    excess_return: float
    excess_return_rate: float


class MetricsCalculator:
    """性能指标计算器"""

    def __init__(self, trading_days_per_year: int = 244, risk_free_rate: float = 0.03):
        self.trading_days_per_year = trading_days_per_year
        self.risk_free_rate = risk_free_rate

    def calculate_all(self,
                     initial_capital: float,
                     final_capital: float,
                     equity_curve: List[Dict],
                     trade_records: List[TradeRecord],
                     price_curve: List[Dict],
                     grid_count: int) -> tuple[PerformanceMetrics, BenchmarkComparison]:
        """
        计算所有指标

        Args:
            initial_capital: 期初资金
            final_capital: 期末资金
            equity_curve: 资产曲线
            trade_records: 交易记录
            price_curve: 价格曲线
            grid_count: 网格总数

        Returns:
            (性能指标, 基准对比)
        """
        # 计算收益指标
        total_return = self._calculate_total_return(initial_capital, final_capital)
        trading_days = self._get_trading_days(equity_curve)
        annualized_return = self._calculate_annualized_return(total_return, trading_days)
        absolute_profit = final_capital - initial_capital

        # 计算风险指标
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        daily_returns = self._calculate_daily_returns(equity_curve)
        volatility = self._calculate_volatility(daily_returns)
        sharpe_ratio = self._calculate_sharpe_ratio(annualized_return, volatility)

        # 计算交易指标
        buy_trades = sum(1 for t in trade_records if t.type == 'BUY')
        sell_trades = sum(1 for t in trade_records if t.type == 'SELL')
        win_rate = self._calculate_win_rate(trade_records)
        profit_loss_ratio = self._calculate_profit_loss_ratio(trade_records)
        grid_trigger_rate = self._calculate_grid_trigger_rate(trade_records, grid_count)

        # 计算基准对比
        benchmark = self._calculate_benchmark(price_curve, total_return)

        metrics = PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            absolute_profit=absolute_profit,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            volatility=volatility,
            total_trades=len(trade_records),
            buy_trades=buy_trades,
            sell_trades=sell_trades,
            win_rate=win_rate,
            profit_loss_ratio=profit_loss_ratio,
            grid_trigger_rate=grid_trigger_rate
        )

        return metrics, benchmark

    def _calculate_total_return(self, initial: float, final: float) -> float:
        """计算总收益率"""
        return (final - initial) / initial

    def _calculate_annualized_return(self, total_return: float, trading_days: int) -> float:
        """计算年化收益率"""
        if trading_days == 0:
            return 0.0
        return total_return * (self.trading_days_per_year / trading_days)

    def _calculate_max_drawdown(self, equity_curve: List[Dict]) -> float:
        """计算最大回撤"""
        if not equity_curve:
            return 0.0

        peak = equity_curve[0]['total_asset']
        max_dd = 0.0

        for point in equity_curve:
            asset = point['total_asset']
            peak = max(peak, asset)
            drawdown = (peak - asset) / peak if peak > 0 else 0
            max_dd = max(max_dd, drawdown)

        return -max_dd  # 返回负值表示回撤

    def _calculate_volatility(self, daily_returns: List[float]) -> float:
        """计算波动率（年化）"""
        if len(daily_returns) < 2:
            return 0.0

        std = np.std(daily_returns, ddof=1)
        return std * np.sqrt(self.trading_days_per_year)

    def _calculate_sharpe_ratio(self, annualized_return: float, volatility: float) -> Optional[float]:
        """计算夏普比率"""
        if volatility == 0:
            return None

        return (annualized_return - self.risk_free_rate) / volatility

    def _calculate_daily_returns(self, equity_curve: List[Dict]) -> List[float]:
        """计算日收益率序列"""
        if len(equity_curve) < 2:
            return []

        returns = []
        for i in range(1, len(equity_curve)):
            prev_asset = equity_curve[i-1]['total_asset']
            curr_asset = equity_curve[i]['total_asset']
            if prev_asset > 0:
                returns.append((curr_asset - prev_asset) / prev_asset)

        return returns

    def _calculate_win_rate(self, trade_records: List[TradeRecord]) -> float:
        """计算胜率"""
        profitable_trades = sum(1 for t in trade_records
                               if t.profit is not None and t.profit > 0)
        total_trades = sum(1 for t in trade_records if t.profit is not None)

        return profitable_trades / total_trades if total_trades > 0 else 0.0

    def _calculate_profit_loss_ratio(self, trade_records: List[TradeRecord]) -> Optional[float]:
        """计算盈亏比"""
        profits = [t.profit for t in trade_records if t.profit is not None and t.profit > 0]
        losses = [abs(t.profit) for t in trade_records if t.profit is not None and t.profit < 0]

        if not profits or not losses:
            return None

        avg_profit = sum(profits) / len(profits)
        avg_loss = sum(losses) / len(losses)

        return avg_profit / avg_loss if avg_loss > 0 else None

    def _calculate_grid_trigger_rate(self, trade_records: List[TradeRecord],
                                    grid_count: int) -> float:
        """计算网格触发率"""
        triggered_prices = set(t.price for t in trade_records)
        return len(triggered_prices) / grid_count if grid_count > 0 else 0.0

    def _calculate_benchmark(self, price_curve: List[Dict],
                           grid_return: float) -> BenchmarkComparison:
        """计算基准对比"""
        if len(price_curve) < 2:
            return BenchmarkComparison(0.0, 0.0, 0.0)

        initial_price = price_curve[0]['close']
        final_price = price_curve[-1]['close']

        hold_return = (final_price - initial_price) / initial_price
        excess_return = grid_return - hold_return
        excess_return_rate = excess_return / hold_return if hold_return != 0 else 0.0

        return BenchmarkComparison(
            hold_return=hold_return,
            excess_return=excess_return,
            excess_return_rate=excess_return_rate
        )

    def _get_trading_days(self, equity_curve: List[Dict]) -> int:
        """获取实际交易日数量"""
        if not equity_curve:
            return 0

        # 通过时间戳计算交易日
        dates = set()
        for point in equity_curve:
            dates.add(point['time'].date())

        return len(dates)
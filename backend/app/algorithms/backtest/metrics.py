"""
回测性能指标计算器

实现完整的性能指标计算体系，包括收益指标、风险指标、交易指标和基准对比。
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import timedelta
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
    capital_utilization_rate: float


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
        capital_utilization_rate = self._calculate_capital_utilization_rate(trade_records, equity_curve, initial_capital)

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
            grid_trigger_rate=grid_trigger_rate,
            capital_utilization_rate=capital_utilization_rate
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
        """
        计算配对交易胜率
        
        基于FIFO原则匹配买入和卖出交易，计算配对交易的胜率。
        这种方法更适合网格交易策略，能够真实反映策略的盈利能力。
        
        Returns:
            float: 配对交易胜率 (0.0 - 1.0)
        """
        return self._calculate_paired_win_rate(trade_records)
    
    def _calculate_paired_win_rate(self, trade_records: List[TradeRecord]) -> float:
        """
        配对交易胜率计算
        
        使用FIFO（先进先出）原则匹配买入和卖出交易：
        1. 按时间排序所有交易
        2. 维护买入队列，每次卖出时从最早的买入开始匹配
        3. 计算每个配对的净盈亏（包含双向手续费）
        4. 统计盈利配对的比例
        
        Args:
            trade_records: 交易记录列表
            
        Returns:
            float: 配对交易胜率
        """
        if not trade_records:
            return 0.0
        
        # 按时间排序交易记录
        sorted_trades = sorted(trade_records, key=lambda x: x.time)
        
        # 买入队列：存储 (买入价格, 数量, 手续费)
        buy_queue = []
        paired_profits = []
        
        for trade in sorted_trades:
            if trade.type == 'BUY':
                # 买入交易加入队列
                buy_queue.append({
                    'price': trade.price,
                    'quantity': trade.quantity,
                    'commission': trade.commission,
                    'time': trade.time
                })
            
            elif trade.type == 'SELL' and buy_queue:
                # 卖出交易，与买入队列配对
                sell_quantity = trade.quantity
                sell_price = trade.price
                sell_commission = trade.commission
                
                # 从最早的买入开始匹配
                while sell_quantity > 0 and buy_queue:
                    buy_record = buy_queue[0]
                    
                    # 确定本次配对的数量
                    paired_quantity = min(sell_quantity, buy_record['quantity'])
                    
                    # 计算配对交易的净盈亏
                    buy_cost = buy_record['price'] * paired_quantity
                    sell_revenue = sell_price * paired_quantity
                    
                    # 按比例分摊手续费
                    buy_commission_portion = (buy_record['commission'] * 
                                            paired_quantity / buy_record['quantity'])
                    sell_commission_portion = (sell_commission * 
                                             paired_quantity / trade.quantity)
                    
                    # 净盈亏 = 卖出收入 - 买入成本 - 总手续费
                    net_profit = (sell_revenue - buy_cost - 
                                buy_commission_portion - sell_commission_portion)
                    
                    paired_profits.append(net_profit)
                    
                    # 更新队列和剩余数量
                    buy_record['quantity'] -= paired_quantity
                    sell_quantity -= paired_quantity
                    
                    # 如果买入记录已完全匹配，从队列中移除
                    if buy_record['quantity'] == 0:
                        buy_queue.pop(0)
        
        # 计算胜率
        if not paired_profits:
            return 0.0
        
        profitable_pairs = sum(1 for profit in paired_profits if profit > 0)
        total_pairs = len(paired_profits)
        
        return profitable_pairs / total_pairs

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

    def _calculate_capital_utilization_rate(self, trade_records: List[TradeRecord],
                                          equity_curve: List[Dict], 
                                          initial_capital: float) -> float:
        """
        计算时间加权的资金利用率
        
        资金利用率 = 1 - (时间加权平均现金余额 / 总资金)
        
        使用时间加权方式计算平均现金余额，考虑每个现金状态持续的时间长度。
        时间单位按天计算，同一天内的交易取平均值。
        
        Args:
            trade_records: 交易记录，包含每次交易后的现金余额
            equity_curve: 资产曲线，用于确定回测时间范围
            initial_capital: 初始资金
            
        Returns:
            float: 资金利用率 (0.0 - 1.0)
        """
        if initial_capital <= 0:
            return 0.0
        
        # 如果没有交易记录，利用率为0（未投资）
        if not trade_records:
            return 0.0
        
        # 如果没有资产曲线，无法确定时间范围，回退到简单平均
        if not equity_curve:
            cash_samples = [initial_capital] + [trade.cash for trade in trade_records]
            avg_cash = sum(cash_samples) / len(cash_samples)
            return max(0.0, min(1.0, 1 - (avg_cash / initial_capital)))
        
        # 确定回测时间范围
        start_time = equity_curve[0]['time']
        end_time = equity_curve[-1]['time']
        
        # 按时间排序交易记录
        sorted_trades = sorted(trade_records, key=lambda x: x.time)
        
        # 构建现金余额时间序列：[(日期, 现金余额)]
        cash_timeline = []
        
        # 添加初始状态（回测开始时的现金）
        start_date = start_time.date()
        cash_timeline.append((start_date, initial_capital))
        
        # 按天聚合交易记录，同一天内取最后的现金余额
        daily_cash = {}
        for trade in sorted_trades:
            trade_date = trade.time.date()
            daily_cash[trade_date] = trade.cash
        
        # 将每日现金余额添加到时间序列
        for date, cash in sorted(daily_cash.items()):
            # 如果与起始日期相同，更新起始现金；否则添加新记录
            if date == start_date:
                cash_timeline[0] = (date, cash)
            else:
                cash_timeline.append((date, cash))
        
        # 计算时间加权平均现金余额
        if len(cash_timeline) == 1:
            # 只有一个时间点，直接使用该现金余额
            time_weighted_avg_cash = cash_timeline[0][1]
        else:
            total_weighted_cash = 0.0
            end_date = end_time.date()
            total_days = (end_date - start_date).days + 1
            
            if total_days <= 0:
                # 时间范围异常，回退到简单平均
                cash_values = [cash for _, cash in cash_timeline]
                time_weighted_avg_cash = sum(cash_values) / len(cash_values)
            else:
                # 计算每个时间段的加权现金
                for i in range(len(cash_timeline)):
                    current_date, current_cash = cash_timeline[i]
                    
                    # 确定当前状态的结束日期
                    if i < len(cash_timeline) - 1:
                        next_date = cash_timeline[i + 1][0]
                        period_end = next_date
                    else:
                        # 最后一个状态持续到回测结束
                        period_end = end_date + timedelta(days=1)  # 包含结束日期
                    
                    # 计算持续天数
                    duration_days = (period_end - current_date).days
                    
                    # 确保持续天数为正
                    if duration_days > 0:
                        weight = duration_days / total_days
                        total_weighted_cash += current_cash * weight
                
                time_weighted_avg_cash = total_weighted_cash
        
        # 资金利用率 = 1 - (时间加权平均现金余额 / 总资金)
        utilization_rate = 1 - (time_weighted_avg_cash / initial_capital)
        
        # 确保利用率在合理范围内 (0-1)
        return max(0.0, min(1.0, utilization_rate))

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
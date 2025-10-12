"""
回测业务服务

整合数据获取、回测执行、指标计算，提供统一的回测业务接口。
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
from app.algorithms.backtest.engine import BacktestEngine
from app.algorithms.backtest.metrics import MetricsCalculator
from app.algorithms.backtest.models import BacktestConfig
from app.services.data_service import DataService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BacktestService:
    """回测业务服务"""

    def __init__(self):
        self.data_service = DataService()

    def run_backtest(self, etf_code: str, exchange_code: str, grid_strategy: dict,
                     backtest_config: Optional[dict] = None, type: str = 'STOCK',
                     country: str = 'CHN') -> Dict:
        """
        执行回测

        Args:
            etf_code: ETF代码
            exchange_code: 交易所代码
            grid_strategy: 网格策略参数
            backtest_config: 回测配置（可选）
            type: 证券类型 ('STOCK' 或 'ETF')
            country: 市场国家代码 ('CHN', 'HKG', 'USA')

        Returns:
            回测结果
        """
        try:
            # 1. 准备回测配置
            config = self._prepare_config(backtest_config)

            # 2. 获取交易日历
            trading_days = self.data_service.get_trading_calendar(
                exchange_code, limit=30
            )

            if not trading_days:
                raise ValueError("无法获取交易日历")

            start_date = trading_days[-1]
            end_date = trading_days[0]

            # 3. 获取K线数据
            kline_data = self.data_service.get_5min_kline(
                etf_code, exchange_code, start_date, end_date, type
            )

            if not kline_data:
                raise ValueError(f"无法获取K线数据: {start_date} - {end_date}")

            logger.info(f"获取到 {len(kline_data)} 条K线数据")

            # 4. 执行回测（传递country参数）
            engine = BacktestEngine(grid_strategy, config, country=country)
            backtest_result = engine.run(kline_data)

            # 5. 计算性能指标
            metrics_calc = MetricsCalculator(
                trading_days_per_year=config.trading_days_per_year,
                risk_free_rate=config.risk_free_rate
            )

            initial_capital = (
                grid_strategy['fund_allocation']['base_position_amount'] +
                grid_strategy['fund_allocation']['grid_trading_amount']
            )

            metrics, benchmark = metrics_calc.calculate_all(
                initial_capital=initial_capital,
                final_capital=backtest_result['final_state']['total_asset'],
                equity_curve=backtest_result['equity_curve'],
                trade_records=backtest_result['trade_records'],
                price_curve=[{'close': k.close} for k in kline_data],
                grid_count=grid_strategy['grid_config']['count']
            )

            # 6. 格式化返回结果
            return self._format_result(
                backtest_result=backtest_result,
                metrics=metrics,
                benchmark=benchmark,
                start_date=start_date,
                end_date=end_date,
                trading_days=len(trading_days),
                kline_data=kline_data,
                grid_strategy=grid_strategy
            )

        except Exception as e:
            logger.error(f"回测执行失败: {str(e)}", exc_info=True)
            raise

    def _prepare_config(self, backtest_config: Optional[dict]) -> BacktestConfig:
        """准备回测配置"""
        if not backtest_config:
            return BacktestConfig()

        return BacktestConfig(
            commission_rate=backtest_config.get('commissionRate', 0.0002),
            min_commission=backtest_config.get('minCommission', 5.0),
            risk_free_rate=backtest_config.get('riskFreeRate', 0.03),
            trading_days_per_year=backtest_config.get('tradingDaysPerYear', 244)
        )


    def _format_result(self, backtest_result: Dict, metrics, benchmark,
                       start_date: str, end_date: str, trading_days: int,
                       kline_data: list, grid_strategy: dict = None) -> Dict:
        """格式化回测结果"""
        # 计算网格分析（如果提供了网格策略）
        grid_analysis = None
        if grid_strategy and 'price_levels' in grid_strategy:
            grid_analysis = self._analyze_grid_performance(
                backtest_result['trade_records'],
                grid_strategy['price_levels']
            )

        return {
            'backtest_period': {
                'start_date': start_date,
                'end_date': end_date,
                'trading_days': trading_days,
                'total_bars': len(kline_data)
            },
            'performance_metrics': {
                'total_return': round(metrics.total_return, 4),
                'annualized_return': round(metrics.annualized_return, 4),
                'absolute_profit': round(metrics.absolute_profit, 2),
                'max_drawdown': round(metrics.max_drawdown, 4),
                'sharpe_ratio': round(metrics.sharpe_ratio, 2) if metrics.sharpe_ratio else None,
                'volatility': round(metrics.volatility, 4)
            },
            'trading_metrics': {
                'total_trades': metrics.total_trades,
                'buy_trades': metrics.buy_trades,
                'sell_trades': metrics.sell_trades,
                'win_rate': round(metrics.win_rate, 4),
                'profit_loss_ratio': round(metrics.profit_loss_ratio, 2) if metrics.profit_loss_ratio else None,
                'grid_trigger_rate': round(metrics.grid_trigger_rate, 4)
            },
            'benchmark_comparison': {
                'hold_return': round(benchmark.hold_return, 4),
                'excess_return': round(benchmark.excess_return, 4),
                'excess_return_rate': round(benchmark.excess_return_rate, 4)
            },
            'equity_curve': self._format_equity_curve(backtest_result['equity_curve']),
            'price_curve': self._format_price_curve(kline_data),
            'trade_records': self._format_trade_records(backtest_result['trade_records']),
            'grid_analysis': grid_analysis,
            'final_state': backtest_result['final_state']
        }

    def _format_equity_curve(self, equity_curve: list) -> list:
        """格式化资产曲线"""
        return [
            {
                'time': point['time'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(point['time'], 'strftime') else point['time'],
                'total_asset': round(point['total_asset'], 2)
            }
            for point in equity_curve
        ]

    def _format_price_curve(self, kline_data: list) -> list:
        """格式化价格曲线"""
        return [
            {
                'time': k.time.strftime('%Y-%m-%d %H:%M:%S'),
                'open': float(k.open),
                'high': float(k.high),
                'low': float(k.low),
                'close': float(k.close),
                'volume': int(k.volume)
            }
            for k in kline_data
        ]

    def _analyze_grid_performance(self, trade_records: list, price_levels: list) -> dict:
        """分析网格表现"""
        if not price_levels:
            return None

        grid_performance = []
        triggered_grids = 0

        for price in price_levels:
            # 统计在该价格附近（±1%）的交易次数
            price_tolerance = price * 0.01  # 1%的容差
            trigger_count = 0
            profit_contribution = 0.0

            for trade in trade_records:
                if abs(trade.price - price) <= price_tolerance:
                    trigger_count += 1
                    if trade.profit is not None:
                        profit_contribution += trade.profit

            grid_performance.append({
                'price': round(price, 3),
                'trigger_count': trigger_count,
                'profit_contribution': round(profit_contribution, 2)
            })

            if trigger_count > 0:
                triggered_grids += 1

        return {
            'grid_performance': grid_performance,
            'triggered_grids': triggered_grids,
            'total_grids': len(price_levels)
        }

    def _format_trade_records(self, trade_records: list) -> list:
        """格式化交易记录"""
        return [
            {
                'time': t.time.strftime('%Y-%m-%d %H:%M:%S'),
                'type': t.type,
                'price': round(t.price, 3),
                'quantity': t.quantity,
                'commission': round(t.commission, 2),
                'profit': round(t.profit, 2) if t.profit is not None else None,
                'position': t.position,
                'cash': round(t.cash, 2)
            }
            for t in trade_records
        ]
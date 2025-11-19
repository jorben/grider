"""
回测业务服务

整合数据获取、回测执行、指标计算，提供统一的回测业务接口。
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
from app.algorithms.backtest.engine import BacktestEngine
from app.algorithms.backtest.metrics import MetricsCalculator
from app.algorithms.backtest.models import BacktestConfig
from app.algorithms.grid.optimizer import GridOptimizer
from app.services.data_service import DataService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BacktestService:
    """回测业务服务"""

    def __init__(self):
        self.data_service = DataService()

    def run_backtest(self, etf_code: str, exchange_code: str, grid_strategy: dict,
                     backtest_config: Optional[dict] = None, type: str = 'STOCK',
                     country: str = 'CHN', custom_grid_params: Optional[dict] = None) -> Dict:
        """
        执行回测

        Args:
            etf_code: ETF代码
            exchange_code: 交易所代码
            grid_strategy: 网格策略参数
            backtest_config: 回测配置（可选）
            type: 证券类型 ('STOCK' 或 'ETF')
            country: 市场国家代码 ('CHN', 'HKG', 'USA')
            custom_grid_params: 自定义网格参数（可选）

        Returns:
            回测结果
        """
        try:
            # 1. 准备回测配置
            config = self._prepare_config(backtest_config)

            # 2. 确定回测日期范围
            if custom_grid_params and 'startDate' in custom_grid_params and 'endDate' in custom_grid_params:
                start_date = custom_grid_params['startDate']
                end_date = custom_grid_params['endDate']
                # 验证日期格式
                try:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                except ValueError:
                    raise ValueError("自定义日期格式无效，应为YYYY-MM-DD")

                # 验证日期范围
                days_diff = (end_dt - start_dt).days
                if days_diff < 30:
                    raise ValueError("回测时间跨度至少30天")
                if days_diff > 120:
                    raise ValueError("回测时间跨度不能超过120天")

                # 获取指定日期范围内的交易日历
                trading_days = self.data_service.get_trading_calendar(
                    exchange_code, start_date=start_date, end_date=end_date
                )
            else:
                # 获取默认的交易日历（最近30个交易日）
                trading_days = self.data_service.get_trading_calendar(
                    exchange_code, limit=30
                )
                if trading_days:
                    start_date = trading_days[-1]
                    end_date = trading_days[0]
                else:
                    raise ValueError("无法获取交易日历")

            logger.info(f"交易日历数据: {trading_days}")
            logger.info(f"使用的日期范围: start_date={start_date}, end_date={end_date}")

            # 3. 获取K线数据
            kline_data = self.data_service.get_5min_kline(
                etf_code, exchange_code, start_date, end_date, type
            )

            if not kline_data:
                raise ValueError(f"无法获取K线数据: {start_date} - {end_date}")

            logger.info(f"获取到 {len(kline_data)} 条K线数据")

            # 4. 如果提供了自定义网格参数，修改网格策略
            if custom_grid_params:
                logger.info(f"应用自定义网格参数: {custom_grid_params}")
                grid_strategy = self._apply_custom_grid_params(grid_strategy, custom_grid_params, country)
                logger.info("已应用自定义网格参数进行回测")
            else:
                logger.info("未提供自定义网格参数，使用默认策略")

            # 6. 执行回测（传递country参数）
            engine = BacktestEngine(grid_strategy, config, country=country)
            backtest_result = engine.run(kline_data)

            # 7. 计算性能指标
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

    def _apply_custom_grid_params(self, grid_strategy: dict, custom_grid_params: dict, country: str = 'CHN') -> dict:
        """应用自定义网格参数到网格策略"""
        optimizer = GridOptimizer(country=country)

        # 提取自定义参数，默认使用原策略参数
        price_lower = custom_grid_params.get('priceLower', grid_strategy['price_range']['lower'])
        price_upper = custom_grid_params.get('priceUpper', grid_strategy['price_range']['upper'])
        benchmark_price = custom_grid_params.get('benchmarkPrice', grid_strategy['current_price'])
        grid_step_value = custom_grid_params.get('gridStepSize', grid_strategy['grid_config']['step_size'])
        total_capital = custom_grid_params.get('totalCapital', grid_strategy['fund_allocation']['base_position_amount'] + grid_strategy['fund_allocation']['grid_trading_amount'])

        # 重新计算价格水平
        grid_type = grid_strategy.get('grid_config', {}).get('type', '等差')
        if grid_type == '等差':
            # 等差网格：grid_step_value 是金额
            price_levels = optimizer.arithmetic_calculator.calculate_grid_levels(
                price_lower, price_upper, grid_step_value, benchmark_price
            )
        else:
            # 等比网格：grid_step_value 是百分比，需要转换为小数
            step_ratio = grid_step_value / 100.0
            price_levels = optimizer.geometric_calculator.calculate_grid_levels(
                price_lower, price_upper, step_ratio, benchmark_price
            )

        # 重新计算资金分配
        fund_allocation = optimizer.calculate_fund_allocation_v2(
            total_capital, price_levels, benchmark_price
        )

        # 允许自定义单笔交易数量，如果未提供则使用计算出的值
        single_trade_quantity = custom_grid_params.get('singleTradeQuantity', fund_allocation.get('single_trade_quantity', grid_strategy['grid_config']['single_trade_quantity']))

        # 更新网格策略
        grid_strategy['price_range'] = {'lower': price_lower, 'upper': price_upper}
        grid_strategy['current_price'] = benchmark_price
        if grid_type == '等差':
            grid_strategy['grid_config']['step_size'] = grid_step_value
        else:
            # For geometric, store as step_ratio (decimal value)
            grid_strategy['grid_config']['step_ratio'] = step_ratio
        grid_strategy['grid_config']['single_trade_quantity'] = single_trade_quantity
        grid_strategy['grid_config']['count'] = len(price_levels)
        grid_strategy['price_levels'] = price_levels
        grid_strategy['fund_allocation'] = fund_allocation

        return grid_strategy


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
                'grid_trigger_rate': round(metrics.grid_trigger_rate, 4),
                'capital_utilization_rate': round(metrics.capital_utilization_rate, 4)
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
            'final_state': backtest_result['final_state'],
            'grid_strategy': grid_strategy  # 包含更新后的网格策略
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
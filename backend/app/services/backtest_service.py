"""
回测业务服务

整合数据获取、回测执行、指标计算，提供统一的回测业务接口。
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
from app.algorithms.backtest.engine import BacktestEngine
from app.algorithms.backtest.ma_engine import MABacktestEngine
from app.algorithms.backtest.metrics import MetricsCalculator
from app.algorithms.backtest.models import BacktestConfig
from app.algorithms.backtest.fee_calculator import FeeCalculator
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
            custom_start = (custom_grid_params or {}).get('startDate') or ''
            custom_end = (custom_grid_params or {}).get('endDate') or ''
            custom_start = custom_start.strip() if isinstance(custom_start, str) else ''
            custom_end = custom_end.strip() if isinstance(custom_end, str) else ''

            if custom_start and custom_end:
                start_date = custom_start
                end_date = custom_end
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
                if days_diff > 3660:
                    raise ValueError("回测时间跨度不能超过10年")

                # 获取指定日期范围内的交易日历
                trading_days = self.data_service.get_trading_calendar(
                    exchange_code, start_date=start_date, end_date=end_date
                )
            else:
                # 未指定（或留空）日期：默认使用最近半年（约182个自然日）
                today = datetime.now()
                default_end = today.strftime('%Y-%m-%d')
                default_start = (today - timedelta(days=182)).strftime('%Y-%m-%d')
                trading_days = self.data_service.get_trading_calendar(
                    exchange_code, start_date=default_start, end_date=default_end
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

            # 网格区间对齐：当回测起始价落在网格区间之外时，以起始价为中心重建网格，
            # 避免 0 底仓 / 0 成交（长周期、自定义日期、历史区间等场景常见）。
            # 注意：仅在"价格完全不重叠"时才重建，用户设定的网格在区间内时予以尊重。
            total_capital = (
                grid_strategy['fund_allocation']['base_position_amount'] +
                grid_strategy['fund_allocation']['grid_trading_amount']
            )
            grid_strategy = self._realign_grid_to_period(
                grid_strategy, kline_data, total_capital, country
            )

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

    def run_ma_backtest(self, etf_code: str, exchange_code: str, ma_params: dict,
                        total_capital: float, backtest_config: Optional[dict] = None,
                        type: str = 'STOCK', country: str = 'CHN',
                        start_date_in: str = '', end_date_in: str = '') -> Dict:
        """执行均线策略回测（趋势跟随：价格上穿均线买入、下穿清仓）。

        Args:
            ma_params: {period, ma_type('SMA'|'EMA')}（单均线全进全出，固定满仓）
            total_capital: 总资金
            start_date_in / end_date_in: 可选自定义日期（YYYY-MM-DD）
        """
        try:
            config = self._prepare_config(backtest_config)

            # 解析回测区间（用户视角的起止）
            start_date, end_date, trading_days = self._resolve_date_range(
                exchange_code, start_date_in, end_date_in
            )

            period = int(ma_params.get('period', 20))

            # 均线预热：在回测开始日之前额外多取 period(+缓冲) 个交易日，
            # 使长周期均线（如128/225日）在回测区间首日即可计算，
            # 预热段只用于喂均线，不参与买卖与收益统计。
            warmup_bars = period + 5
            fetch_start = self._shift_trading_days_back(exchange_code, start_date, warmup_bars)

            # 获取K线（含预热段）
            kline_all = self.data_service.get_5min_kline(
                etf_code, exchange_code, fetch_start, end_date, type
            )
            if not kline_all:
                raise ValueError(f"无法获取K线数据: {fetch_start} - {end_date}")

            # 定位回测段起始下标（第一根 >= start_date 的bar）
            start_cmp = start_date
            trade_start_index = 0
            for idx, kb in enumerate(kline_all):
                if kb.time.strftime('%Y-%m-%d') >= start_cmp:
                    trade_start_index = idx
                    break

            window_len = len(kline_all) - trade_start_index
            logger.info(f"均线回测: 总K线{len(kline_all)}(含预热{trade_start_index}), 回测段{window_len}, 周期{period}")

            # 校验：预热不足以支撑该周期（标的上市时间太短等）
            if trade_start_index < period:
                # 预热段不足 period 根：均线在回测段前期可能缺失，但仍可继续；
                # 仅当连"回测段长度"都不足以判断时才报错。
                if window_len < 2:
                    raise ValueError(f"数据不足以回测{period}日均线，请缩短周期或选更长区间")

            # 执行均线回测（带预热）
            # 手续费按证券类型区分：指数免佣；ETF 去掉最低5元(仅按费率)；个股保留最低5元
            if type == 'INDEX':
                fee_calc = FeeCalculator(commission_rate=0.0, min_commission=0.0, apply_min=False)
            elif type in ('ETF', 'FUND'):
                # ETF/场外基金：按费率计费，不套用个股的最低5元佣金
                fee_calc = FeeCalculator(
                    commission_rate=config.commission_rate,
                    min_commission=config.min_commission,
                    apply_min=False,
                )
            else:  # STOCK
                fee_calc = FeeCalculator(
                    commission_rate=config.commission_rate,
                    min_commission=config.min_commission,
                    apply_min=True,
                )
            engine = MABacktestEngine(ma_params, fee_calc, total_capital, country=country, sec_type=type)
            backtest_result = engine.run(kline_all, trade_start_index=trade_start_index)

            # 仅用回测段（窗口）计算指标与价格基准
            window_kline = kline_all[trade_start_index:]

            metrics_calc = MetricsCalculator(
                trading_days_per_year=config.trading_days_per_year,
                risk_free_rate=config.risk_free_rate,
            )
            metrics, benchmark = metrics_calc.calculate_all(
                initial_capital=total_capital,
                final_capital=backtest_result['final_state']['total_asset'],
                equity_curve=backtest_result['equity_curve'],
                trade_records=backtest_result['trade_records'],
                price_curve=[{'close': k.close} for k in window_kline],
                grid_count=0,
            )

            return self._format_ma_result(
                backtest_result=backtest_result,
                metrics=metrics,
                benchmark=benchmark,
                start_date=start_date,
                end_date=end_date,
                trading_days=len(trading_days),
                kline_data=window_kline,
                ma_params=ma_params,
                ma_series_full=backtest_result.get('ma_series', []),
                trade_start_index=trade_start_index,
            )
        except Exception as e:
            logger.error(f"均线回测执行失败: {str(e)}", exc_info=True)
            raise

    def _shift_trading_days_back(self, exchange_code: str, date_str: str, n_days: int) -> str:
        """返回 date_str 之前第 n_days 个交易日（用于均线预热取数起点）。

        取不到足够交易日历时，按自然日粗略回退兜底。
        """
        try:
            # 取一段足够长的历史交易日历（用大区间，向前覆盖）
            from datetime import datetime as _dt, timedelta as _td
            end = date_str
            # 自然日上预留：n_days 个交易日约等于 n_days*1.5 自然日，再加缓冲
            start = (_dt.strptime(date_str, '%Y-%m-%d') - _td(days=int(n_days * 1.7) + 40)).strftime('%Y-%m-%d')
            cal = self.data_service.get_trading_calendar(
                exchange_code, start_date=start, end_date=end
            )
            # cal 为降序（最新在前），且包含 <= date_str 的交易日
            cal_sorted = sorted(set(cal))  # 升序
            # 只保留 < date_str 的交易日作为预热
            before = [d for d in cal_sorted if d < date_str]
            if len(before) >= n_days:
                return before[-n_days]
            if before:
                return before[0]
            # 兜底：自然日回退
            return start
        except Exception as e:  # noqa: BLE001
            logger.warning(f"计算预热起始日失败，使用自然日兜底: {e}")
            from datetime import datetime as _dt, timedelta as _td
            return (_dt.strptime(date_str, '%Y-%m-%d') - _td(days=int(n_days * 1.7) + 40)).strftime('%Y-%m-%d')

    def _resolve_date_range(self, exchange_code: str, custom_start: str, custom_end: str):
        """解析回测日期范围，返回 (start_date, end_date, trading_days)。"""
        custom_start = custom_start.strip() if isinstance(custom_start, str) else ''
        custom_end = custom_end.strip() if isinstance(custom_end, str) else ''

        if custom_start and custom_end:
            try:
                start_dt = datetime.strptime(custom_start, '%Y-%m-%d')
                end_dt = datetime.strptime(custom_end, '%Y-%m-%d')
            except ValueError:
                raise ValueError("自定义日期格式无效，应为YYYY-MM-DD")
            days_diff = (end_dt - start_dt).days
            if days_diff < 30:
                raise ValueError("回测时间跨度至少30天")
            if days_diff > 3660:
                raise ValueError("回测时间跨度不能超过10年")
            trading_days = self.data_service.get_trading_calendar(
                exchange_code, start_date=custom_start, end_date=custom_end
            )
            return custom_start, custom_end, trading_days

        # 默认最近半年
        today = datetime.now()
        default_end = today.strftime('%Y-%m-%d')
        default_start = (today - timedelta(days=182)).strftime('%Y-%m-%d')
        trading_days = self.data_service.get_trading_calendar(
            exchange_code, start_date=default_start, end_date=default_end
        )
        if not trading_days:
            raise ValueError("无法获取交易日历")
        return trading_days[-1], trading_days[0], trading_days

    def _format_ma_result(self, backtest_result: Dict, metrics, benchmark,
                          start_date: str, end_date: str, trading_days: int,
                          kline_data: list, ma_params: dict,
                          ma_series_full: list = None, trade_start_index: int = 0) -> Dict:
        """格式化均线回测结果（结构对齐网格回测，便于前端复用）。

        kline_data 为回测段（窗口）K线；ma_series_full 为含预热段的完整均线序列，
        需切片到窗口对齐后返回，使前端均线曲线与窗口价格曲线一一对应。
        """
        # 将完整均线序列切片到回测窗口
        if ma_series_full is None:
            ma_series_full = backtest_result.get('ma_series', [])
        ma_window = ma_series_full[trade_start_index:] if ma_series_full else []
        ma_curve = [
            {
                'time': k.time.strftime('%Y-%m-%d %H:%M:%S'),
                'ma': round(ma, 3) if ma is not None else None,
            }
            for k, ma in zip(kline_data, ma_window)
        ]
        return {
            'strategy_type': 'ma',
            'ma_config': {
                'period': int(ma_params.get('period', 20)),
                'ma_type': ma_params.get('ma_type', 'SMA'),
            },
            'backtest_period': {
                'start_date': start_date,
                'end_date': end_date,
                'trading_days': trading_days,
                'total_bars': len(kline_data),
            },
            'performance_metrics': {
                'total_return': round(metrics.total_return, 4),
                'annualized_return': round(metrics.annualized_return, 4),
                'absolute_profit': round(metrics.absolute_profit, 2),
                'max_drawdown': round(metrics.max_drawdown, 4),
                'sharpe_ratio': round(metrics.sharpe_ratio, 2) if metrics.sharpe_ratio else None,
                'volatility': round(metrics.volatility, 4),
            },
            'trading_metrics': {
                'total_trades': metrics.total_trades,
                'buy_trades': metrics.buy_trades,
                'sell_trades': metrics.sell_trades,
                'win_rate': round(metrics.win_rate, 4),
                'profit_loss_ratio': round(metrics.profit_loss_ratio, 2) if metrics.profit_loss_ratio else None,
                'capital_utilization_rate': round(metrics.capital_utilization_rate, 4),
            },
            'benchmark_comparison': {
                'hold_return': round(benchmark.hold_return, 4),
                'excess_return': round(benchmark.excess_return, 4),
                'excess_return_rate': round(benchmark.excess_return_rate, 4),
            },
            'equity_curve': self._format_equity_curve(backtest_result['equity_curve']),
            'price_curve': self._format_price_curve(kline_data),
            'ma_curve': ma_curve,
            'trade_records': self._format_trade_records(backtest_result['trade_records']),
            'final_state': backtest_result['final_state'],
        }

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

    def _realign_grid_to_period(self, grid_strategy: dict, kline_data: list,
                                total_capital: float, country: str = 'CHN') -> dict:
        """回测网格区间对齐。

        分析阶段网格以"最新价"为中心构建，但回测回放的是历史区间，
        其起始价格可能落在网格区间之外，导致初始建仓为 0、全程无成交。
        此处检测：若回测首根K线均价不在 [lower, upper] 内，则以该价格为
        新基准价，按原步长重建等距/等比网格，使回测真实可交易。
        """
        try:
            if not kline_data:
                return grid_strategy

            first = kline_data[0]
            start_price = (first.high + first.low + first.open + first.close) / 4

            price_range = grid_strategy.get('price_range', {})
            lower = price_range.get('lower')
            upper = price_range.get('upper')
            if lower is None or upper is None:
                return grid_strategy

            # 起始价格在区间内则无需调整
            if lower <= start_price <= upper:
                return grid_strategy

            logger.warning(
                f"回测起始价{start_price:.3f}超出分析网格[{lower:.3f}, {upper:.3f}]，"
                f"以起始价为中心重建网格"
            )

            optimizer = GridOptimizer(country=country)
            grid_config = grid_strategy.get('grid_config', {})
            grid_type = grid_config.get('type', '等差')

            # 保持原网格宽度比例，围绕新基准价重建上下边界
            half_width_ratio = (upper - lower) / 2 / grid_strategy.get('current_price', start_price)
            new_lower = round(start_price * (1 - half_width_ratio), 3)
            new_upper = round(start_price * (1 + half_width_ratio), 3)

            if grid_type == '等差':
                step = grid_config.get('step_size', round(start_price * 0.01, 4))
                price_levels = optimizer.arithmetic_calculator.calculate_grid_levels(
                    new_lower, new_upper, step, start_price
                )
            else:
                step_ratio = grid_config.get('step_ratio', 0.01)
                price_levels = optimizer.geometric_calculator.calculate_grid_levels(
                    new_lower, new_upper, start_price * step_ratio, start_price
                )

            fund_allocation = optimizer.calculate_fund_allocation_v2(
                total_capital, price_levels, start_price,
                forced_single_quantity=grid_config.get('single_trade_quantity')
            )

            grid_strategy['current_price'] = round(start_price, 3)
            grid_strategy['price_range'] = {
                'lower': new_lower,
                'upper': new_upper,
                'ratio': round((new_upper - new_lower) / start_price, 4) if start_price else None,
            }
            grid_strategy['price_levels'] = price_levels
            grid_strategy['grid_config']['count'] = len(price_levels)
            grid_strategy['grid_config']['single_trade_quantity'] = fund_allocation.get(
                'single_trade_quantity', grid_strategy['grid_config'].get('single_trade_quantity', 100)
            )
            grid_strategy['fund_allocation'] = fund_allocation
            grid_strategy['realigned_to_period'] = True
            grid_strategy['total_capital'] = round(total_capital, 2)

            return grid_strategy
        except Exception as e:  # noqa: BLE001
            logger.error(f"回测网格区间对齐失败，使用原网格: {e}")
            return grid_strategy

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
            step_ratio = (grid_step_value / benchmark_price) if benchmark_price else 0
            price_levels = optimizer.arithmetic_calculator.calculate_grid_levels(
                price_lower, price_upper, grid_step_value, benchmark_price
            )
        else:
            # 等比网格：grid_step_value 是百分比(如15表示15%)。
            # calculate_grid_levels 第三个参数要求"绝对步长(元)"，内部再除以基准价得到比例，
            # 故此处必须传 绝对步长 = 基准价 × 百分比/100，否则会被二次缩放（15%→0.75%）。
            step_ratio = grid_step_value / 100.0
            abs_step = benchmark_price * step_ratio
            price_levels = optimizer.geometric_calculator.calculate_grid_levels(
                price_lower, price_upper, abs_step, benchmark_price
            )

        # 用户可显式指定单笔数量；传入优化器以正确反推底仓与资金占用（不被静默覆盖）
        forced_qty = custom_grid_params.get('singleTradeQuantity')
        forced_qty = int(forced_qty) if forced_qty else None

        # 重新计算资金分配（尊重用户单笔数量）
        fund_allocation = optimizer.calculate_fund_allocation_v2(
            total_capital, price_levels, benchmark_price,
            forced_single_quantity=forced_qty
        )

        # 单笔数量：以优化器最终采用的值为准（已包含用户指定或反推结果），
        # 保证 grid_config 与 fund_allocation 两处一致。
        single_trade_quantity = fund_allocation.get(
            'single_trade_quantity',
            grid_strategy['grid_config'].get('single_trade_quantity', 100)
        )

        # 更新网格策略
        grid_strategy['price_range'] = {
            'lower': price_lower,
            'upper': price_upper,
            'ratio': round((price_upper - price_lower) / benchmark_price, 4) if benchmark_price else None,
        }
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
        # 显式记录本次回测实际使用的总资金，供前端统一显示，避免三个标签口径不一致
        grid_strategy['total_capital'] = round(total_capital, 2)

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

        result = {
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

        # 方案A：基于回测实测结果生成适宜度评估，保证三个标签同源一致
        try:
            from app.services.backtest_suitability import evaluate_from_backtest
            result['suitability_evaluation'] = evaluate_from_backtest(
                result['performance_metrics'],
                result['benchmark_comparison'],
                result['trading_metrics'],
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"基于回测的适宜度评估失败（忽略）: {e}")

        return result

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
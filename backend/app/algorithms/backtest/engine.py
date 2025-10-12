"""
回测引擎核心

负责编排整个回测流程，包括数据处理、交易执行、结果汇总等。
"""

from typing import List, Dict
from datetime import datetime
from .models import KBar, TradeRecord, BacktestState, BacktestConfig
from .trading_logic import TradingLogic
from .fee_calculator import FeeCalculator


class BacktestEngine:
    """回测引擎核心"""

    def __init__(self, grid_strategy: dict, backtest_config: BacktestConfig, country: str = 'CHN'):
        self.grid_strategy = grid_strategy
        self.config = backtest_config
        self.country = country

        # 初始化手续费计算器
        self.fee_calc = FeeCalculator(
            commission_rate=backtest_config.commission_rate,
            min_commission=backtest_config.min_commission
        )

        # 初始化交易逻辑（传递country参数）
        self.trading_logic = TradingLogic(
            grid_config=grid_strategy['grid_config'],
            fee_calculator=self.fee_calc,
            country=country  # 传递country参数
        )

        # 状态追踪
        self.state: BacktestState = None
        self.trade_records: List[TradeRecord] = []
        self.equity_curve: List[Dict] = []

    def run(self, kline_data: List[KBar]) -> Dict:
        """
        执行回测

        Args:
            kline_data: K线数据列表

        Returns:
            回测结果
        """
        if not kline_data:
            raise ValueError("K线数据为空")

        # 1. 获取资金配置
        fund_alloc = self.grid_strategy['fund_allocation']
        total_capital = fund_alloc['base_position_amount'] + fund_alloc['grid_trading_amount']

        # 2. 执行初始底仓购买（使用第一根K线）
        first_kbar = kline_data[0]
        self.state, initial_trade = self.trading_logic.execute_initial_position(
            first_kbar=first_kbar,
            base_position_amount=fund_alloc['base_position_amount'],
            total_capital=total_capital,
            strategy_base_price=self.grid_strategy['current_price'],
            price_lower=self.grid_strategy['price_range']['lower'],
            price_upper=self.grid_strategy['price_range']['upper']
        )

        # 记录初始建仓交易
        if initial_trade:
            self.trade_records.append(initial_trade)

        # 3. 逐K线扫描交易（从第一根K线开始，不跳过）
        for kbar in kline_data:
            # 更新总资产（按收盘价）
            self.state.total_asset = self.state.cash + self.state.position * kbar.close
            self.state.peak_asset = max(self.state.peak_asset, self.state.total_asset)

            # 记录资产曲线
            self._record_equity_point(kbar.time, kbar.close)

            # 检查并执行交易
            new_state, trade_record = self.trading_logic.check_and_execute(
                self.state, kbar
            )

            if trade_record:
                trade_record.time = kbar.time
                self.trade_records.append(trade_record)
                self.state = new_state

        # 4. 返回回测结果
        return self._generate_result(kline_data)

    def _record_equity_point(self, time: datetime, price: float):
        """记录资产曲线点"""
        self.equity_curve.append({
            'time': time,
            'total_asset': self.state.total_asset,
            'price': price
        })

    def _generate_result(self, kline_data: List[KBar]) -> Dict:
        """生成回测结果"""
        return {
            'trade_records': self.trade_records,
            'equity_curve': self.equity_curve,
            'final_state': {
                'cash': self.state.cash,
                'position': self.state.position,
                'total_asset': self.state.total_asset
            },
            'kline_data': kline_data
        }
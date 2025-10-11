"""
回测算法数据模型定义

使用dataclass定义核心数据结构，确保类型安全和代码简洁。
"""

from dataclasses import dataclass
from typing import List, Literal
from datetime import datetime


@dataclass
class KBar:
    """K线数据"""
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class TradeRecord:
    """交易记录"""
    time: datetime
    type: Literal['BUY', 'SELL']
    price: float
    quantity: int
    commission: float
    profit: float | None
    position: int
    cash: float


@dataclass
class BacktestState:
    """回测状态"""
    cash: float                    # 可用资金
    position: int                  # 持仓股数
    base_price: float             # 当前基准价
    buy_price: float              # 当前买入点
    sell_price: float             # 当前卖出点
    total_asset: float            # 总资产
    peak_asset: float             # 峰值资产
    price_lower: float            # 价格下限
    price_upper: float            # 价格上限


@dataclass
class BacktestConfig:
    """回测配置"""
    commission_rate: float = 0.0002   # 手续费率
    min_commission: float = 5.0        # 最低收费
    risk_free_rate: float = 0.03       # 无风险利率
    trading_days_per_year: int = 244   # 年交易日数
"""
ETF网格交易回测算法模块

本模块包含回测引擎核心组件：
- BacktestEngine: 回测引擎核心
- TradingLogic: 网格交易逻辑
- FeeCalculator: 手续费计算器
- 数据模型定义
"""

from .engine import BacktestEngine
from .trading_logic import TradingLogic
from .fee_calculator import FeeCalculator
from .models import KBar, TradeRecord, BacktestState, BacktestConfig

__all__ = [
    'BacktestEngine',
    'TradingLogic',
    'FeeCalculator',
    'KBar',
    'TradeRecord',
    'BacktestState',
    'BacktestConfig'
]
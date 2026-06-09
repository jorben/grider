# ETF网格交易回测功能 - 阶段2实施方案

## 📋 需求整体背景

在ETF网格交易策略分析系统中新增**回测分析**功能，基于已生成的网格参数，使用历史5分钟K线数据进行策略回测，帮助用户评估策略的历史表现。完整功能包括：

- 基于5分钟K线数据的回测引擎 ✅ (阶段1已完成)
- 网格交易逻辑的精确模拟 ✅ (阶段1已完成)
- 多维度性能指标计算（收益、风险、交易指标）← 本阶段重点
- 可视化展示（图表、交易记录、网格分析）
- 支持参数调整和多周期对比

**总体技术架构**：
- 后端：Python Flask + 回测算法引擎
- 前端：React + Recharts图表库
- 数据源：TickFlowProvider（5分钟K线）+ exchange_calendars 离线库（交易日历）

---

## 🎯 当前所处阶段

**阶段2：后端指标计算与API开发**

本阶段基于阶段1完成的回测引擎，实现**完整的性能指标计算体系**和**API接口层**，为前端提供标准化的回测数据。

### 阶段1成果回顾

- ✅ [`BacktestEngine`](backend/app/algorithms/backtest/engine.py) - 回测引擎核心
- ✅ [`TradingLogic`](backend/app/algorithms/backtest/trading_logic.py) - 交易逻辑
- ✅ [`FeeCalculator`](backend/app/algorithms/backtest/fee_calculator.py) - 手续费计算器
- ✅ 扩展的[`DataService`](backend/app/services/data_service.py) - 支持5分钟K线

---

## 🚀 当前阶段目标

### 主要目标

1. **实现性能指标计算器**
   - 收益指标：总收益率、年化收益率、绝对收益
   - 风险指标：最大回撤、夏普比率、波动率
   - 交易指标：交易次数、胜率、盈亏比、网格触发率
   - 基准对比：持有不动收益、超额收益

2. **创建回测业务服务**
   - 整合数据获取、回测执行、指标计算
   - 实现完整的业务流程编排
   - 提供统一的错误处理

3. **开发API接口**
   - 创建`POST /api/grid/backtest`端点
   - 定义标准请求/响应格式
   - 实现参数验证和异常处理

4. **优化数据结构**
   - 格式化输出符合前端要求
   - 实现数据缓存机制
   - 优化响应性能

### 交付物

- ✅ 指标计算器模块（含单元测试）
- ✅ BacktestService业务服务
- ✅ API路由和控制器
- ✅ 标准化响应数据格式
- ✅ 集成测试（端到端流程）
- ✅ API文档

---

## 📝 详细实施计划

### 任务1：实现指标计算器（5小时）

#### 1.1 创建MetricsCalculator类
在[`backend/app/algorithms/backtest/metrics.py`](backend/app/algorithms/backtest/metrics.py)中实现：

```python
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
```

#### 1.2 编写指标计算器测试
在[`backend/tests/test_metrics.py`](backend/tests/test_metrics.py)中：

```python
import pytest
from datetime import datetime, timedelta
from app.algorithms.backtest.metrics import MetricsCalculator, PerformanceMetrics
from app.algorithms.backtest.models import TradeRecord

@pytest.fixture
def equity_curve():
    base_time = datetime(2025, 1, 10, 9, 30)
    return [
        {'time': base_time, 'total_asset': 10000, 'price': 3.50},
        {'time': base_time + timedelta(days=1), 'total_asset': 10100, 'price': 3.51},
        {'time': base_time + timedelta(days=2), 'total_asset': 10050, 'price': 3.49},
        {'time': base_time + timedelta(days=3), 'total_asset': 10200, 'price': 3.52},
        {'time': base_time + timedelta(days=4), 'total_asset': 10300, 'price': 3.53},
    ]

def test_total_return_calculation():
    """测试总收益率计算"""
    calc = MetricsCalculator()
    total_return = calc._calculate_total_return(10000, 10300)
    assert total_return == 0.03  # 3%

def test_max_drawdown_calculation(equity_curve):
    """测试最大回撤计算"""
    calc = MetricsCalculator()
    max_dd = calc._calculate_max_drawdown(equity_curve)
    # 从10100回撤到10050，回撤率 = (10100-10050)/10100 ≈ 0.495%
    assert -0.01 < max_dd < 0.0

def test_win_rate_calculation():
    """测试胜率计算"""
    calc = MetricsCalculator()
    trades = [
        TradeRecord(datetime.now(), 'SELL', 3.5, 100, 0.35, 10, 700, 10000),
        TradeRecord(datetime.now(), 'SELL', 3.5, 100, 0.35, -5, 700, 10000),
        TradeRecord(datetime.now(), 'SELL', 3.5, 100, 0.35, 8, 700, 10000),
    ]
    win_rate = calc._calculate_win_rate(trades)
    assert win_rate == 2/3  # 66.67%
```

### 任务2：创建回测业务服务（4小时）

#### 2.1 创建BacktestService
在[`backend/app/services/backtest_service.py`](backend/app/services/backtest_service.py)中实现：

```python
from typing import Dict, Optional
from datetime import datetime, timedelta
from app.algorithms.backtest.engine import BacktestEngine
from app.algorithms.backtest.metrics import MetricsCalculator
from app.algorithms.backtest.models import BacktestConfig
from app.services.data_service import DataService
from app.utils.logger import logger

class BacktestService:
    """回测业务服务"""
    
    def __init__(self):
        self.data_service = DataService()
    
    def run_backtest(self, etf_code: str, grid_strategy: dict, 
                    backtest_config: Optional[dict] = None) -> Dict:
        """
        执行回测
        
        Args:
            etf_code: ETF代码
            grid_strategy: 网格策略参数
            backtest_config: 回测配置（可选）
            
        Returns:
            回测结果
        """
        try:
            # 1. 准备回测配置
            config = self._prepare_config(backtest_config)
            
            # 2. 获取交易日历
            exchange_code = self._get_exchange_code(etf_code)
            trading_days = self.data_service.get_trading_calendar(
                exchange_code, limit=5
            )
            
            if not trading_days:
                raise ValueError("无法获取交易日历")
            
            start_date = trading_days[-1]
            end_date = trading_days[0]
            
            # 3. 获取K线数据
            kline_data = self.data_service.get_5min_kline(
                etf_code, exchange_code, start_date, end_date
            )
            
            if not kline_data:
                raise ValueError(f"无法获取K线数据: {start_date} - {end_date}")
            
            logger.info(f"获取到 {len(kline_data)} 条K线数据")
            
            # 4. 执行回测
            engine = BacktestEngine(grid_strategy, config)
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
                kline_data=kline_data
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
    
    def _get_exchange_code(self, etf_code: str) -> str:
        """根据ETF代码获取交易所代码"""
        if etf_code.startswith('5'):
            return 'SH'  # 上海
        elif etf_code.startswith('1') or etf_code.startswith('15'):
            return 'SZ'  # 深圳
        else:
            return 'SH'  # 默认上海
    
    def _format_result(self, backtest_result: Dict, metrics, benchmark,
                      start_date: str, end_date: str, trading_days: int,
                      kline_data: list) -> Dict:
        """格式化回测结果"""
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
            'final_state': backtest_result['final_state']
        }
    
    def _format_equity_curve(self, equity_curve: list) -> list:
        """格式化资产曲线"""
        return [
            {
                'time': point['time'].strftime('%Y-%m-%d %H:%M:%S'),
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
```

### 任务3：开发API接口（3小时）

#### 3.1 扩展网格路由
在[`backend/app/routes/grid_routes.py`](backend/app/routes/grid_routes.py)中添加：

```python
from flask import Blueprint, request, jsonify
from app.services.backtest_service import BacktestService
from app.utils.validation import validate_backtest_request
from app.utils.logger import logger

grid_bp = Blueprint('grid', __name__)

# ... 现有路由 ...

@grid_bp.route('/backtest', methods=['POST'])
def run_backtest():
    """
    执行网格策略回测
    
    请求格式:
    {
        "etfCode": "510300",
        "gridStrategy": {...},
        "backtestConfig": {...}
    }
    """
    try:
        # 1. 获取并验证请求参数
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求参数不能为空'
            }), 400
        
        # 验证必需字段
        validation_result = validate_backtest_request(data)
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': validation_result['error']
            }), 400
        
        etf_code = data.get('etfCode')
        grid_strategy = data.get('gridStrategy')
        backtest_config = data.get('backtestConfig')
        
        # 2. 执行回测
        backtest_service = BacktestService()
        result = backtest_service.run_backtest(
            etf_code=etf_code,
            grid_strategy=grid_strategy,
            backtest_config=backtest_config
        )
        
        # 3. 返回结果
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except ValueError as e:
        logger.warning(f"参数验证错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"回测执行异常: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '回测执行失败，请稍后重试'
        }), 500
```

#### 3.2 添加请求验证
在[`backend/app/utils/validation.py`](backend/app/utils/validation.py)中扩展：

```python
def validate_backtest_request(data: dict) -> dict:
    """
    验证回测请求参数
    
    Args:
        data: 请求数据
        
    Returns:
        {'valid': bool, 'error': str}
    """
    # 验证ETF代码
    if 'etfCode' not in data:
        return {'valid': False, 'error': '缺少etfCode参数'}
    
    # 验证网格策略
    if 'gridStrategy' not in data:
        return {'valid': False, 'error': '缺少gridStrategy参数'}
    
    grid_strategy = data['gridStrategy']
    
    # 验证必需字段
    required_fields = [
        'current_price', 'price_range', 'grid_config', 'fund_allocation'
    ]
    
    for field in required_fields:
        if field not in grid_strategy:
            return {'valid': False, 'error': f'网格策略缺少{field}字段'}
    
    # 验证回测配置（可选）
    if 'backtestConfig' in data:
        config = data['backtestConfig']
        
        # 验证费率范围
        if 'commissionRate' in config:
            rate = config['commissionRate']
            if not (0 <= rate <= 1):
                return {'valid': False, 'error': '手续费率必须在0-1之间'}
        
        # 验证最低收费
        if 'minCommission' in config:
            min_fee = config['minCommission']
            if min_fee < 0:
                return {'valid': False, 'error': '最低收费不能为负'}
    
    return {'valid': True, 'error': None}
```

### 任务4：集成测试（3小时）

#### 4.1 端到端测试
在[`backend/tests/test_backtest_integration.py`](backend/tests/test_backtest_integration.py)中：

```python
import pytest
from app import create_app
from app.services.backtest_service import BacktestService

@pytest.fixture
def app():
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def sample_request():
    return {
        'etfCode': '510300',
        'gridStrategy': {
            'current_price': 3.500,
            'price_range': {
                'lower': 3.200,
                'upper': 3.800
            },
            'grid_config': {
                'count': 20,
                'type': '等差',
                'step_size': 0.030,
                'single_trade_quantity': 100
            },
            'fund_allocation': {
                'base_position_amount': 2500.00,
                'base_position_shares': 700,
                'grid_trading_amount': 7000.00
            }
        },
        'backtestConfig': {
            'commissionRate': 0.0002,
            'minCommission': 5.0,
            'riskFreeRate': 0.03,
            'tradingDaysPerYear': 244
        }
    }

def test_backtest_api_success(client, sample_request):
    """测试回测API成功场景"""
    response = client.post(
        '/api/grid/backtest',
        json=sample_request
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'data' in data
    
    result = data['data']
    assert 'backtest_period' in result
    assert 'performance_metrics' in result
    assert 'trading_metrics' in result
    assert 'trade_records' in result

def test_backtest_api_missing_params(client):
    """测试缺少参数的情况"""
    response = client.post(
        '/api/grid/backtest',
        json={}
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'error' in data

def test_backtest_service_integration():
    """测试BacktestService集成"""
    service = BacktestService()
    
    grid_strategy = {
        'current_price': 3.500,
        'price_range': {'lower': 3.200, 'upper': 3.800},
        'grid_config': {
            'count': 20,
            'type': '等差',
            'step_size': 0.030,
            'single_trade_quantity': 100
        },
        'fund_allocation': {
            'base_position_amount': 2500.00,
            'base_position_shares': 700,
            'grid_trading_amount': 7000.00
        }
    }
    
    # 注意：此测试依赖真实数据源，可能需要mock
    result = service.run_backtest('510300', grid_strategy)
    
    assert 'backtest_period' in result
    assert result['backtest_period']['trading_days'] > 0
```

### 任务5：API文档编写（2小时）

#### 5.1 创建API文档
在[`docs/api/backtest.md`](docs/api/backtest.md)中：

```markdown
# 回测API文档

## 执行回测

### 请求

- **URL**: `/api/grid/backtest`
- **方法**: `POST`
- **Content-Type**: `application/json`

### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| etfCode | string | 是 | ETF代码 |
| gridStrategy | object | 是 | 网格策略参数 |
| backtestConfig | object | 否 | 回测配置参数 |

#### gridStrategy 结构

```json
{
  "current_price": 3.500,
  "price_range": {
    "lower": 3.200,
    "upper": 3.800
  },
  "grid_config": {
    "count": 20,
    "type": "等差",
    "step_size": 0.030,
    "single_trade_quantity": 100
  },
  "fund_allocation": {
    "base_position_amount": 2500.00,
    "base_position_shares": 700,
    "grid_trading_amount": 7000.00
  }
}
```

#### backtestConfig 结构（可选）

```json
{
  "commissionRate": 0.0002,
  "minCommission": 5.0,
  "riskFreeRate": 0.03,
  "tradingDaysPerYear": 244
}
```

### 响应示例

#### 成功响应 (200)

```json
{
  "success": true,
  "data": {
    "backtest_period": {...},
    "performance_metrics": {...},
    "trading_metrics": {...},
    "benchmark_comparison": {...},
    "equity_curve": [...],
    "price_curve": [...],
    "trade_records": [...],
    "final_state": {...}
  }
}
```

#### 错误响应 (400)

```json
{
  "success": false,
  "error": "参数验证失败：缺少etfCode参数"
}
```

#### 服务器错误 (500)

```json
{
  "success": false,
  "error": "回测执行失败，请稍后重试"
}
```
```

---

## 🔍 阶段实施准则

### 代码质量标准

1. **指标计算准确性**
   - 所有公式严格按需求文档实现
   - 边界条件特殊处理（除零、空数据等）
   - 计算结果保留合理精度

2. **服务层设计**
   - 单一职责原则
   - 依赖注入
   - 完善的异常处理
   - 日志记录关键操作

3. **API设计**
   - RESTful规范
   - 统一的响应格式
   - 详细的错误信息
   - 参数验证完善

4. **测试覆盖**
   - 单元测试覆盖所有指标计算
   - 集成测试覆盖完整流程
   - Mock外部依赖
   - 边界条件测试

### 开发流程

1. **开发顺序**
   ```
   指标计算器 → 业务服务 → API接口 → 验证层 → 集成测试 → API文档
   ```

2. **提交规范**
   ```
   feat: 实现性能指标计算器
   feat: 创建回测业务服务
   feat: 添加回测API接口
   test: 添加端到端集成测试
   docs: 完善回测API文档
   ```

3. **代码审查要点**
   - 计算公式正确性
   - 异常处理完整性
   - 响应格式一致性
   - 测试用例覆盖度

### 性能要求

- API响应时间 < 3秒（5天数据）
- 指标计算耗时 < 100ms
- 支持并发请求数 ≥ 10
- 内存占用 < 200MB

---

## ✅ 成果验收计划

### 功能验收

| 验收项 | 验收标准 | 验收方法 |
|--------|---------|---------|
| 收益指标计算 | 总收益率、年化收益率、绝对收益准确 | 单元测试 + 手工验证 |
| 风险指标计算 | 最大回撤、夏普比率、波动率准确 | 与标准算法对比 |
| 交易指标计算 | 交易次数、胜率、盈亏比准确 | 实际案例验证 |
| 基准对比 | 持有不动收益、超额收益计算正确 | 场景测试 |
| API功能 | 接口正常响应，数据格式正确 | Postman测试 |
| 错误处理 | 异常情况正确处理和返回 | 异常场景测试 |

### 质量验收

- ✅ 单元测试覆盖率 ≥ 85%
- ✅ 集成测试通过率 100%
- ✅ API文档完整准确
- ✅ 代码符合规范
- ✅ 性能指标达标

### 交付清单

- [ ] [`metrics.py`](backend/app/algorithms/backtest/metrics.py) - 指标计算器
- [ ] [`backtest_service.py`](backend/app/services/backtest_service.py) - 业务服务
- [ ] 扩展的[`grid_routes.py`](backend/app/routes/grid_routes.py) - API路由
- [ ] 扩展的[`validation.py`](backend/app/utils/validation.py) - 参数验证
- [ ] 完整的测试文件
- [ ] API文档

### 验收方式

1. **单元测试验收**
   ```bash
   pytest backend/tests/test_metrics.py -v --cov
   pytest backend/tests/test_backtest_service.py -v --cov
   pytest backend/tests/test_validation.py -v
   ```

2. **集成测试验收**
   ```bash
   pytest backend/tests/test_backtest_integration.py -v
   ```

3. **API功能验收**
   - 使用Postman测试完整流程
   - 验证响应数据格式
   - 测试异常场景处理
   - 性能压力测试

4. **数据准确性验证**
   - 准备标准测试案例
   - 手工计算预期结果
   - 对比API返回结果
   - 确认误差在容许范围

---

## 📌 注意事项

1. **指标计算精度**
   - 中间计算保留足够精度
   - 最终结果合理四舍五入
   - 避免浮点数累积误差

2. **空数据处理**
   - 交易记录为空时胜率为0
   - 无亏损交易时盈亏比为None
   - 波动率为0时夏普比率为None

3. **日期处理**
   - 统一使用ISO 8601格式
   - 正确处理时区
   - 交易日计算准确

4. **API响应优化**
   - 大数据量分页处理
   - 非必要数据延迟加载
   - 考虑缓存策略

5. **错误信息**
   - 区分用户错误和系统错误
   - 提供可操作的错误提示
   - 记录详细日志便于排查

---

## 🔗 与其他阶段的衔接

### 阶段1提供的基础

- ✅ 回测引擎和交易逻辑
- ✅ 交易记录数据结构
- ✅ 资产曲线追踪
- ✅ 数据获取服务

### 本阶段交付给阶段3

- ✅ 完整的API接口
- ✅ 标准化的JSON响应格式
- ✅ 详细的API文档
- ✅ 错误码定义

### 阶段3需要实现

- 前端组件开发
- 图表可视化
- 用户交互逻辑
- 响应式布局

---

**文档版本**：v1.0  
**创建时间**：2025-01-10  
**预计工时**：17小时  
**负责团队**：后端服务组
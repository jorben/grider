# ETF网格交易回测功能 - 阶段1实施方案

## 📋 需求整体背景

在ETF网格交易策略分析系统中新增**回测分析**功能，基于已生成的网格参数，使用历史5分钟K线数据进行策略回测，帮助用户评估策略的历史表现。完整功能包括：

- 基于5分钟K线数据的回测引擎
- 网格交易逻辑的精确模拟
- 多维度性能指标计算（收益、风险、交易指标）
- 可视化展示（图表、交易记录、网格分析）
- 支持参数调整和多周期对比

**总体技术架构**：
- 后端：Python Flask + 回测算法引擎
- 前端：React + Recharts图表库
- 数据源：TsanghiProvider（5分钟K线 + 交易日历）

---

## 🎯 当前所处阶段

**阶段1：后端核心回测引擎开发**

本阶段是整个回测功能的**基础核心**，专注于构建回测计算引擎，实现网格交易逻辑的精确模拟。后续阶段将基于此引擎进行扩展。

---

## 🚀 当前阶段目标

### 主要目标

1. **构建回测引擎核心框架**
   - 创建[`BacktestEngine`](backend/app/algorithms/backtest/engine.py)类，负责回测流程编排
   - 实现K线数据的时序遍历机制
   - 建立状态管理系统（持仓、资金、基准价等）

2. **实现网格交易逻辑**
   - 实现初始建仓逻辑（底仓建仓 + 价格偏离处理）
   - 实现买卖信号判断（基于网格点触发）
   - 实现成交执行与状态更新
   - 支持等差/等比两种网格类型

3. **实现手续费计算**
   - 创建[`FeeCalculator`](backend/app/algorithms/backtest/fee_calculator.py)类
   - 支持费率和最低收费配置
   - 准确计算每笔交易成本

4. **集成数据服务**
   - 扩展[`DataService`](backend/app/services/data_service.py)获取5分钟K线数据
   - 集成交易日历获取功能
   - 实现数据格式标准化

### 交付物

- ✅ 完整的回测引擎代码（含单元测试）
- ✅ 手续费计算器（含边界测试）
- ✅ 数据服务扩展（支持5分钟K线）
- ✅ 核心算法单元测试（覆盖率≥80%）
- ✅ 技术文档（算法说明、接口定义）

---

## 📝 详细实施计划

### 任务1：创建回测模块基础结构（2小时）

#### 1.1 创建目录结构
```bash
backend/app/algorithms/backtest/
├── __init__.py
├── engine.py           # 回测引擎核心
├── trading_logic.py    # 交易逻辑
├── fee_calculator.py   # 手续费计算器
└── models.py           # 数据模型定义
```

#### 1.2 定义核心数据模型
在[`models.py`](backend/app/algorithms/backtest/models.py)中定义：

```python
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
    
@dataclass
class BacktestConfig:
    """回测配置"""
    commission_rate: float = 0.0002   # 手续费率
    min_commission: float = 5.0        # 最低收费
    risk_free_rate: float = 0.03       # 无风险利率
    trading_days_per_year: int = 244   # 年交易日数
```

### 任务2：实现手续费计算器（1小时）

#### 2.1 创建FeeCalculator类
在[`fee_calculator.py`](backend/app/algorithms/backtest/fee_calculator.py)中实现：

```python
class FeeCalculator:
    """手续费计算器"""
    
    def __init__(self, commission_rate: float = 0.0002, min_commission: float = 5.0):
        """
        初始化手续费计算器
        
        Args:
            commission_rate: 费率（默认0.02%）
            min_commission: 最低收费（默认5元）
        """
        self.commission_rate = commission_rate
        self.min_commission = min_commission
    
    def calculate(self, amount: float) -> float:
        """
        计算手续费
        
        Args:
            amount: 成交金额
            
        Returns:
            实际手续费
        """
        commission = amount * self.commission_rate
        return max(commission, self.min_commission)
    
    def calculate_buy_cost(self, price: float, quantity: int) -> float:
        """计算买入总成本（含手续费）"""
        amount = price * quantity
        commission = self.calculate(amount)
        return amount + commission
    
    def calculate_sell_income(self, price: float, quantity: int) -> float:
        """计算卖出实际收入（扣除手续费）"""
        amount = price * quantity
        commission = self.calculate(amount)
        return amount - commission
```

#### 2.2 编写单元测试
在[`backend/tests/test_fee_calculator.py`](backend/tests/test_fee_calculator.py)中：

```python
import pytest
from app.algorithms.backtest.fee_calculator import FeeCalculator

def test_normal_commission():
    """测试正常手续费计算"""
    calc = FeeCalculator(commission_rate=0.0002, min_commission=5.0)
    
    # 1000元成交额，手续费应为0.2元，但不低于5元
    assert calc.calculate(1000.0) == 5.0
    
    # 100000元成交额，手续费应为20元
    assert calc.calculate(100000.0) == 20.0

def test_buy_cost():
    """测试买入成本计算"""
    calc = FeeCalculator()
    cost = calc.calculate_buy_cost(price=10.0, quantity=100)
    # 成本 = 1000 + 5 = 1005
    assert cost == 1005.0

def test_sell_income():
    """测试卖出收入计算"""
    calc = FeeCalculator()
    income = calc.calculate_sell_income(price=10.0, quantity=100)
    # 收入 = 1000 - 5 = 995
    assert income == 995.0
```

### 任务3：实现网格交易逻辑（4小时）

#### 3.1 创建TradingLogic类
在[`trading_logic.py`](backend/app/algorithms/backtest/trading_logic.py)中实现：

```python
from typing import Tuple, Optional
from .models import BacktestState, KBar, TradeRecord
from .fee_calculator import FeeCalculator
import math

class TradingLogic:
    """网格交易逻辑"""
    
    def __init__(self, grid_config: dict, fee_calculator: FeeCalculator):
        self.grid_config = grid_config
        self.fee_calc = fee_calculator
        self.grid_type = grid_config['type']
        self.step_size = grid_config.get('step_size', 0)
        self.step_ratio = grid_config.get('step_ratio', 0)
        self.single_quantity = grid_config['single_trade_quantity']
    
    def initialize_position(self, base_price: float, base_shares: int, 
                          total_capital: float) -> BacktestState:
        """
        初始化底仓建仓
        
        Args:
            base_price: 基准价格
            base_shares: 底仓股数
            total_capital: 总资金
            
        Returns:
            初始状态
        """
        # 计算建仓成本
        base_cost = self.fee_calc.calculate_buy_cost(base_price, base_shares)
        
        # 初始化状态
        cash = total_capital - base_cost
        position = base_shares
        
        # 计算初始买卖点
        buy_price, sell_price = self._calculate_grid_prices(base_price)
        
        total_asset = cash + position * base_price
        
        return BacktestState(
            cash=cash,
            position=position,
            base_price=base_price,
            buy_price=buy_price,
            sell_price=sell_price,
            total_asset=total_asset,
            peak_asset=total_asset
        )
    
    def handle_price_deviation(self, state: BacktestState, 
                               actual_price: float) -> Tuple[BacktestState, List[TradeRecord]]:
        """
        处理价格偏离（倍数成交机制）
        
        Args:
            state: 当前状态
            actual_price: 实际价格
            
        Returns:
            (更新后的状态, 交易记录列表)
        """
        records = []
        
        # 计算偏离档位
        deviation = math.floor((state.base_price - actual_price) / 
                              (self.step_size if self.grid_type == '等差' 
                               else state.base_price * self.step_ratio))
        
        if deviation > 0:
            # 触发N倍买入
            for _ in range(deviation):
                if state.cash >= self.fee_calc.calculate_buy_cost(
                    actual_price, self.single_quantity):
                    state, record = self._execute_buy(state, actual_price)
                    records.append(record)
        elif deviation < 0:
            # 触发|N|倍卖出
            for _ in range(abs(deviation)):
                if state.position >= self.single_quantity:
                    state, record = self._execute_sell(state, actual_price)
                    records.append(record)
        
        return state, records
    
    def check_and_execute(self, state: BacktestState, 
                         kbar: KBar) -> Tuple[BacktestState, Optional[TradeRecord]]:
        """
        检查并执行交易
        
        Args:
            state: 当前状态
            kbar: K线数据
            
        Returns:
            (更新后的状态, 交易记录或None)
        """
        # 检查买入条件
        if kbar.low <= state.buy_price:
            required_cash = self.fee_calc.calculate_buy_cost(
                state.buy_price, self.single_quantity)
            if state.cash >= required_cash:
                return self._execute_buy(state, state.buy_price)
        
        # 检查卖出条件
        if kbar.high >= state.sell_price:
            if state.position >= self.single_quantity:
                return self._execute_sell(state, state.sell_price)
        
        return state, None
    
    def _execute_buy(self, state: BacktestState, 
                    price: float) -> Tuple[BacktestState, TradeRecord]:
        """执行买入"""
        cost = self.fee_calc.calculate_buy_cost(price, self.single_quantity)
        commission = cost - price * self.single_quantity
        
        # 更新状态
        state.cash -= cost
        state.position += self.single_quantity
        state.base_price = price
        state.buy_price, state.sell_price = self._calculate_grid_prices(price)
        state.total_asset = state.cash + state.position * price
        state.peak_asset = max(state.peak_asset, state.total_asset)
        
        # 创建交易记录
        record = TradeRecord(
            time=datetime.now(),  # 实际使用K线时间
            type='BUY',
            price=price,
            quantity=self.single_quantity,
            commission=commission,
            profit=None,
            position=state.position,
            cash=state.cash
        )
        
        return state, record
    
    def _execute_sell(self, state: BacktestState, 
                     price: float) -> Tuple[BacktestState, TradeRecord]:
        """执行卖出"""
        income = self.fee_calc.calculate_sell_income(price, self.single_quantity)
        commission = price * self.single_quantity - income
        
        # 计算盈亏（需要找到对应的买入成本）
        # 简化处理：用平均成本估算
        avg_cost = (state.total_asset - state.cash) / state.position if state.position > 0 else price
        profit = (price - avg_cost) * self.single_quantity - commission
        
        # 更新状态
        state.cash += income
        state.position -= self.single_quantity
        state.base_price = price
        state.buy_price, state.sell_price = self._calculate_grid_prices(price)
        state.total_asset = state.cash + state.position * price
        state.peak_asset = max(state.peak_asset, state.total_asset)
        
        # 创建交易记录
        record = TradeRecord(
            time=datetime.now(),
            type='SELL',
            price=price,
            quantity=self.single_quantity,
            commission=commission,
            profit=profit,
            position=state.position,
            cash=state.cash
        )
        
        return state, record
    
    def _calculate_grid_prices(self, base_price: float) -> Tuple[float, float]:
        """计算网格买卖点"""
        if self.grid_type == '等差':
            buy_price = base_price - self.step_size
            sell_price = base_price + self.step_size
        else:  # 等比
            buy_price = base_price * (1 - self.step_ratio)
            sell_price = base_price * (1 + self.step_ratio)
        
        return buy_price, sell_price
```

### 任务4：实现回测引擎核心（4小时）

#### 4.1 创建BacktestEngine类
在[`engine.py`](backend/app/algorithms/backtest/engine.py)中实现：

```python
from typing import List, Dict
from datetime import datetime
from .models import KBar, TradeRecord, BacktestState, BacktestConfig
from .trading_logic import TradingLogic
from .fee_calculator import FeeCalculator

class BacktestEngine:
    """回测引擎核心"""
    
    def __init__(self, grid_strategy: dict, backtest_config: BacktestConfig):
        self.grid_strategy = grid_strategy
        self.config = backtest_config
        
        # 初始化手续费计算器
        self.fee_calc = FeeCalculator(
            commission_rate=backtest_config.commission_rate,
            min_commission=backtest_config.min_commission
        )
        
        # 初始化交易逻辑
        self.trading_logic = TradingLogic(
            grid_config=grid_strategy['grid_config'],
            fee_calculator=self.fee_calc
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
        
        # 1. 初始化建仓
        fund_alloc = self.grid_strategy['fund_allocation']
        total_capital = fund_alloc['base_position_amount'] + fund_alloc['grid_trading_amount']
        
        self.state = self.trading_logic.initialize_position(
            base_price=self.grid_strategy['current_price'],
            base_shares=fund_alloc['base_position_shares'],
            total_capital=total_capital
        )
        
        # 记录初始状态
        self._record_equity_point(kline_data[0].time, kline_data[0].close)
        
        # 2. 处理价格偏离（如果存在）
        first_price = kline_data[0].close
        if abs(first_price - self.grid_strategy['current_price']) > 0.01:
            self.state, deviation_trades = self.trading_logic.handle_price_deviation(
                self.state, first_price
            )
            self.trade_records.extend(deviation_trades)
        
        # 3. 逐K线扫描交易
        for kbar in kline_data:
            # 检查并执行交易
            new_state, trade_record = self.trading_logic.check_and_execute(
                self.state, kbar
            )
            
            if trade_record:
                trade_record.time = kbar.time
                self.trade_records.append(trade_record)
                self.state = new_state
            
            # 更新总资产（按收盘价）
            self.state.total_asset = self.state.cash + self.state.position * kbar.close
            self.state.peak_asset = max(self.state.peak_asset, self.state.total_asset)
            
            # 记录资产曲线
            self._record_equity_point(kbar.time, kbar.close)
        
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
```

### 任务5：扩展数据服务（3小时）

#### 5.1 扩展DataService
在[`backend/app/services/data_service.py`](backend/app/services/data_service.py)中添加：

```python
from datetime import datetime, timedelta
from typing import List, Dict
from app.algorithms.backtest.models import KBar

class DataService:
    # ... 现有代码 ...
    
    def get_5min_kline(self, ticker: str, exchange_code: str, 
                       start_date: str, end_date: str) -> List[KBar]:
        """
        获取5分钟K线数据
        
        Args:
            ticker: 标的代码
            exchange_code: 交易所代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            K线数据列表
        """
        # 判断标的类型（ETF或股票）
        if ticker.startswith('5') or ticker.startswith('1'):
            # ETF
            data = self.provider.get_etf_5min(ticker, exchange_code, start_date, end_date)
        else:
            # 股票
            data = self.provider.get_stock_5min(ticker, exchange_code, start_date, end_date)
        
        # 转换为KBar对象
        kbars = []
        for row in data:
            kbars.append(KBar(
                time=datetime.strptime(row['date'], '%Y-%m-%d %H:%M:%S'),
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row['volume'])
            ))
        
        return kbars
    
    def get_trading_calendar(self, exchange_code: str, limit: int = 5) -> List[str]:
        """
        获取最近N个交易日
        
        Args:
            exchange_code: 交易所代码
            limit: 获取天数
            
        Returns:
            交易日列表 ['2025-01-16', '2025-01-15', ...]
        """
        calendar_data = self.provider.get_calendar(exchange_code, limit)
        return [row['date'] for row in calendar_data]
```

### 任务6：编写单元测试（3小时）

#### 6.1 测试回测引擎
在[`backend/tests/test_backtest_engine.py`](backend/tests/test_backtest_engine.py)中：

```python
import pytest
from datetime import datetime
from app.algorithms.backtest.engine import BacktestEngine
from app.algorithms.backtest.models import KBar, BacktestConfig

@pytest.fixture
def grid_strategy():
    return {
        'current_price': 3.500,
        'price_range': {'lower': 3.200, 'upper': 3.800},
        'grid_config': {
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

@pytest.fixture
def kline_data():
    base_time = datetime(2025, 1, 10, 9, 30)
    return [
        KBar(base_time, 3.50, 3.51, 3.49, 3.50, 10000),
        KBar(base_time + timedelta(minutes=5), 3.50, 3.48, 3.46, 3.47, 12000),  # 触发买入
        KBar(base_time + timedelta(minutes=10), 3.47, 3.52, 3.47, 3.51, 11000), # 触发卖出
    ]

def test_backtest_basic_flow(grid_strategy, kline_data):
    """测试基本回测流程"""
    config = BacktestConfig()
    engine = BacktestEngine(grid_strategy, config)
    
    result = engine.run(kline_data)
    
    # 验证交易记录
    assert len(result['trade_records']) >= 2
    assert result['trade_records'][0].type == 'BUY'
    assert result['trade_records'][1].type == 'SELL'
    
    # 验证资产曲线
    assert len(result['equity_curve']) == len(kline_data)
    
    # 验证最终状态
    assert result['final_state']['total_asset'] > 0
```

---

## 🔍 阶段实施准则

### 代码质量标准

1. **类型安全**
   - 所有函数使用类型注解
   - 使用dataclass定义数据模型
   - 关键参数进行验证

2. **错误处理**
   - 使用try-except捕获异常
   - 提供清晰的错误信息
   - 边界条件处理（资金不足、股数不足等）

3. **测试覆盖**
   - 单元测试覆盖率≥80%
   - 包含正常场景和异常场景
   - 关键算法必须有测试用例

4. **文档规范**
   - 每个类和函数都有docstring
   - 说明参数、返回值、异常
   - 复杂逻辑添加注释

### 开发流程

1. **开发顺序**
   ```
   数据模型定义 → 手续费计算器 → 交易逻辑 → 回测引擎 → 数据服务 → 单元测试
   ```

2. **提交规范**
   ```
   feat: 实现手续费计算器
   test: 添加交易逻辑单元测试
   refactor: 优化回测引擎性能
   ```

3. **代码审查**
   - 每个模块完成后自我review
   - 检查类型安全和边界处理
   - 验证测试覆盖率

### 性能要求

- 5天数据（约240根K线）回测时间 < 1秒
- 内存占用 < 100MB
- 支持并发请求（后续阶段）

---

## ✅ 成果验收计划

### 功能验收

| 验收项 | 验收标准 | 验收方法 |
|--------|---------|---------|
| 手续费计算 | 正确计算费用，支持最低收费 | 单元测试通过 |
| 初始建仓 | 正确建立底仓，扣除手续费 | 单元测试 + 手工验证 |
| 价格偏离处理 | 正确触发倍数成交 | 场景测试 |
| 买卖信号判断 | 准确触发网格交易 | 单元测试覆盖边界 |
| 状态更新 | 持仓、资金、基准价正确更新 | 回测流程测试 |
| 数据获取 | 成功获取5分钟K线和交易日历 | 集成测试 |

### 质量验收

- ✅ 单元测试覆盖率 ≥ 80%
- ✅ 所有测试用例通过
- ✅ 代码符合Python PEP8规范
- ✅ 无明显性能瓶颈
- ✅ 错误处理完善

### 交付清单

- [ ] [`engine.py`](backend/app/algorithms/backtest/engine.py) - 回测引擎核心
- [ ] [`trading_logic.py`](backend/app/algorithms/backtest/trading_logic.py) - 交易逻辑
- [ ] [`fee_calculator.py`](backend/app/algorithms/backtest/fee_calculator.py) - 手续费计算器
- [ ] [`models.py`](backend/app/algorithms/backtest/models.py) - 数据模型
- [ ] 扩展后的[`data_service.py`](backend/app/services/data_service.py)
- [ ] 完整的单元测试文件
- [ ] 技术文档（算法说明）

### 验收方式

1. **单元测试验收**
   ```bash
   pytest backend/tests/test_fee_calculator.py -v
   pytest backend/tests/test_trading_logic.py -v
   pytest backend/tests/test_backtest_engine.py -v
   pytest backend/tests/test_data_service.py -v --cov=app.algorithms.backtest
   ```

2. **功能演示**
   - 准备模拟数据
   - 运行回测流程
   - 展示交易记录和最终状态
   - 验证计算准确性

3. **代码审查**
   - 检查代码结构和命名规范
   - 验证类型注解完整性
   - 确认错误处理机制
   - 评估代码可维护性

---

## 📌 注意事项

1. **严格按网格点成交**
   - 成交价格必须是网格点价格
   - 不使用K线的实际高低价

2. **倍数成交机制**
   - 价格偏离时要计算档位
   - 触发N倍买入/卖出
   - 更新基准价为最后成交价

3. **边界处理**
   - 资金不足时跳过买入，不报错
   - 股数不足时跳过卖出，不报错
   - 同时触发时优先买入

4. **等差vs等比**
   - 等差：固定金额步长
   - 等比：固定比例步长
   - 两种模式计算逻辑不同

5. **数据兼容性**
   - 支持ETF和股票数据
   - 处理数据缺失情况
   - 时间格式统一

---

## 🔗 与后续阶段的衔接

### 阶段2依赖项

本阶段为阶段2提供：
- ✅ 完整的回测引擎（可直接调用）
- ✅ 交易记录数据结构
- ✅ 资产曲线数据
- ✅ 数据服务接口

### 阶段2需要实现

- 基于本阶段交易记录计算指标
- 创建BacktestService编排流程
- 实现API端点接收请求
- 返回标准化的JSON响应

---

**文档版本**：v1.0  
**创建时间**：2025-01-10  
**预计工时**：17小时  
**负责团队**：后端算法组
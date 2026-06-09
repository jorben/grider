# ETF网格交易回测功能 - 阶段3实施方案

## 📋 需求整体背景

在ETF网格交易策略分析系统中新增**回测分析**功能，基于已生成的网格参数，使用历史5分钟K线数据进行策略回测，帮助用户评估策略的历史表现。完整功能包括：

- 基于5分钟K线数据的回测引擎 ✅ (阶段1已完成)
- 网格交易逻辑的精确模拟 ✅ (阶段1已完成)
- 多维度性能指标计算 ✅ (阶段2已完成)
- API接口层 ✅ (阶段2已完成)
- 可视化展示（图表、交易记录、网格分析）← 本阶段重点
- 支持参数调整和多周期对比

**总体技术架构**：
- 后端：Python Flask + 回测算法引擎 ✅
- 前端：React + Recharts图表库 ← 本阶段实现
- 数据源：TickFlowProvider（5分钟K线）+ exchange_calendars 离线库（交易日历）✅

---

## 🎯 当前所处阶段

**阶段3：前端基础组件与图表开发**

本阶段基于阶段2完成的API接口，实现**前端可视化展示系统**，包括核心组件、图表展示和交互逻辑。

### 前置阶段成果回顾

**阶段1交付**：
- ✅ 回测引擎核心算法
- ✅ 交易逻辑和手续费计算
- ✅ 数据服务扩展

**阶段2交付**：
- ✅ 性能指标计算器
- ✅ BacktestService业务服务
- ✅ `/api/grid/backtest` API接口
- ✅ 标准化JSON响应格式

---

## 🚀 当前阶段目标

### 主要目标

1. **创建回测标签页结构**
   - 在分析报告中新增"回测分析"标签
   - 创建[`BacktestTab`](frontend/src/features/analysis/components/BacktestTab.jsx)容器组件
   - 建立数据流和状态管理

2. **实现指标展示组件**
   - 创建[`BacktestMetrics`](frontend/src/features/analysis/components/backtest/BacktestMetrics.jsx)指标卡片
   - 展示核心指标（收益、风险、交易）
   - 实现基准对比显示

3. **实现图表可视化**
   - 创建[`BacktestCharts`](frontend/src/features/analysis/components/backtest/BacktestCharts.jsx)双图表组件
   - 主图：价格走势 + 买卖点标注
   - 副图：收益曲线对比
   - 使用Recharts库实现

4. **实现交易记录表格**
   - 创建[`TradeList`](frontend/src/features/analysis/components/backtest/TradeList.jsx)组件
   - 支持类型筛选
   - 展示详细交易信息

5. **API集成**
   - 封装回测API调用
   - 实现加载状态管理
   - 完善错误处理

### 交付物

- ✅ 回测标签页及子组件
- ✅ 指标卡片组件
- ✅ 双图表可视化组件
- ✅ 交易记录列表组件
- ✅ API服务封装
- ✅ 组件单元测试
- ✅ 响应式样式

---

## 📝 详细实施计划

### 任务1：配置依赖和准备工作（1小时）

#### 1.1 安装Recharts
```bash
cd frontend
npm install recharts --save
```

#### 1.2 创建目录结构
```bash
frontend/src/features/analysis/components/backtest/
├── BacktestMetrics.jsx       # 指标卡片
├── BacktestCharts.jsx         # 图表组件
├── TradeList.jsx              # 交易记录
├── GridPerformance.jsx        # 网格分析（阶段4）
└── index.js                   # 导出
```

#### 1.3 扩展API服务
在[`frontend/src/shared/services/api.js`](frontend/src/shared/services/api.js)中添加：

```javascript
/**
 * 执行回测
 * @param {string} etfCode - ETF代码
 * @param {object} gridStrategy - 网格策略参数
 * @param {object} backtestConfig - 回测配置（可选）
 * @returns {Promise<object>} 回测结果
 */
export const runBacktest = async (etfCode, gridStrategy, backtestConfig = null) => {
  try {
    const response = await fetch(`${API_BASE_URL}/grid/backtest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        etfCode,
        gridStrategy,
        backtestConfig,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || '回测执行失败');
    }

    return data.data;
  } catch (error) {
    console.error('回测API调用失败:', error);
    throw error;
  }
};
```

### 任务2：创建回测标签页容器（2小时）

#### 2.1 修改ReportTabs添加标签
在[`frontend/src/features/analysis/components/ReportTabs.jsx`](frontend/src/features/analysis/components/ReportTabs.jsx)中：

```javascript
import React from 'react';

const TABS = [
  { id: 'overview', label: '概览' },
  { id: 'suitability', label: '适宜度评估' },
  { id: 'strategy', label: '网格策略' },
  { id: 'backtest', label: '回测分析' }, // 新增
];

export default function ReportTabs({ activeTab, onTabChange }) {
  return (
    <div className="border-b border-gray-200">
      <nav className="-mb-px flex space-x-8" aria-label="Tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`
              whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
              ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }
            `}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
```

#### 2.2 创建BacktestTab容器组件
在[`frontend/src/features/analysis/components/BacktestTab.jsx`](frontend/src/features/analysis/components/BacktestTab.jsx)中：

```javascript
import React, { useState, useEffect } from 'react';
import { runBacktest } from '@shared/services/api';
import { LoadingSpinner } from '@shared/components/ui';
import BacktestMetrics from './backtest/BacktestMetrics';
import BacktestCharts from './backtest/BacktestCharts';
import TradeList from './backtest/TradeList';

/**
 * 回测分析标签页
 */
export default function BacktestTab({ etfCode, gridStrategy }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [backtestResult, setBacktestResult] = useState(null);
  const [backtestConfig, setBacktestConfig] = useState({
    commissionRate: 0.0002,
    minCommission: 5.0,
    riskFreeRate: 0.03,
    tradingDaysPerYear: 244,
  });

  useEffect(() => {
    if (etfCode && gridStrategy) {
      handleRunBacktest();
    }
  }, [etfCode, gridStrategy]);

  const handleRunBacktest = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await runBacktest(etfCode, gridStrategy, backtestConfig);
      setBacktestResult(result);
    } catch (err) {
      setError(err.message || '回测执行失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <LoadingSpinner size="large" />
        <span className="ml-3 text-gray-600">回测计算中...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">❌ {error}</p>
        <button
          onClick={handleRunBacktest}
          className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          重试
        </button>
      </div>
    );
  }

  if (!backtestResult) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">暂无回测数据</p>
        <button
          onClick={handleRunBacktest}
          className="mt-4 px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          开始回测
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 指标概览 */}
      <BacktestMetrics
        metrics={backtestResult.performance_metrics}
        tradingMetrics={backtestResult.trading_metrics}
        benchmark={backtestResult.benchmark_comparison}
        period={backtestResult.backtest_period}
      />

      {/* 图表展示 */}
      <BacktestCharts
        priceCurve={backtestResult.price_curve}
        equityCurve={backtestResult.equity_curve}
        tradeRecords={backtestResult.trade_records}
        gridStrategy={gridStrategy}
      />

      {/* 交易记录 */}
      <TradeList trades={backtestResult.trade_records} />
    </div>
  );
}
```

### 任务3：实现指标卡片组件（3小时）

#### 3.1 创建BacktestMetrics组件
在[`frontend/src/features/analysis/components/backtest/BacktestMetrics.jsx`](frontend/src/features/analysis/components/backtest/BacktestMetrics.jsx)中：

```javascript
import React from 'react';
import { formatPercent, formatCurrency } from '@shared/utils/format';

/**
 * 回测指标卡片
 */
export default function BacktestMetrics({ metrics, tradingMetrics, benchmark, period }) {
  const coreMetrics = [
    {
      label: '总收益率',
      value: formatPercent(metrics.total_return),
      color: metrics.total_return >= 0 ? 'text-green-600' : 'text-red-600',
      extra: `超额${formatPercent(benchmark.excess_return)}`,
      extraColor: benchmark.excess_return >= 0 ? 'text-green-500' : 'text-red-500',
    },
    {
      label: '年化收益',
      value: formatPercent(metrics.annualized_return),
      color: metrics.annualized_return >= 0 ? 'text-green-600' : 'text-red-600',
    },
    {
      label: '最大回撤',
      value: formatPercent(metrics.max_drawdown),
      color: 'text-red-600',
    },
    {
      label: '夏普比率',
      value: metrics.sharpe_ratio !== null ? metrics.sharpe_ratio.toFixed(2) : 'N/A',
      color: 'text-blue-600',
    },
  ];

  const tradingMetricsData = [
    {
      label: '交易次数',
      value: `${tradingMetrics.total_trades}次`,
    },
    {
      label: '胜率',
      value: formatPercent(tradingMetrics.win_rate),
      color: tradingMetrics.win_rate >= 0.5 ? 'text-green-600' : 'text-gray-600',
    },
    {
      label: '盈亏比',
      value: tradingMetrics.profit_loss_ratio !== null
        ? tradingMetrics.profit_loss_ratio.toFixed(2)
        : 'N/A',
    },
    {
      label: '网格触发率',
      value: formatPercent(tradingMetrics.grid_trigger_rate),
    },
  ];

  return (
    <div className="space-y-4">
      {/* 回测周期 */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-sm text-blue-800">
          📅 回测区间：{period.start_date} ~ {period.end_date} 
          （{period.trading_days}个交易日，{period.total_bars}根K线）
        </p>
      </div>

      {/* 核心指标 */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-4">核心指标</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {coreMetrics.map((metric, index) => (
            <div key={index} className="text-center p-3 bg-gray-50 rounded">
              <p className="text-sm text-gray-600 mb-1">{metric.label}</p>
              <p className={`text-2xl font-bold ${metric.color}`}>{metric.value}</p>
              {metric.extra && (
                <p className={`text-xs mt-1 ${metric.extraColor}`}>▲ {metric.extra}</p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 交易统计 */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-4">交易统计</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {tradingMetricsData.map((metric, index) => (
            <div key={index} className="text-center p-3 bg-gray-50 rounded">
              <p className="text-sm text-gray-600 mb-1">{metric.label}</p>
              <p className={`text-xl font-semibold ${metric.color || 'text-gray-800'}`}>
                {metric.value}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* 基准对比 */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-3">基准对比</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded">
            <p className="text-sm text-gray-600 mb-1">持有不动</p>
            <p className="text-lg font-semibold text-gray-700">
              {formatPercent(benchmark.hold_return)}
            </p>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded">
            <p className="text-sm text-gray-600 mb-1">网格策略</p>
            <p className="text-lg font-semibold text-green-600">
              {formatPercent(metrics.total_return)}
            </p>
          </div>
          <div className="text-center p-3 bg-green-50 rounded">
            <p className="text-sm text-gray-600 mb-1">超额收益</p>
            <p className={`text-lg font-semibold ${
              benchmark.excess_return >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatPercent(benchmark.excess_return)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
```

### 任务4：实现图表组件（5小时）

#### 4.1 创建BacktestCharts组件
在[`frontend/src/features/analysis/components/backtest/BacktestCharts.jsx`](frontend/src/features/analysis/components/backtest/BacktestCharts.jsx)中：

```javascript
import React from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Scatter,
  ComposedChart,
} from 'recharts';

/**
 * 回测图表组件
 */
export default function BacktestCharts({ priceCurve, equityCurve, tradeRecords, gridStrategy }) {
  // 合并价格和交易数据
  const priceData = priceCurve.map((bar, index) => {
    const buyTrades = tradeRecords.filter(
      (t) => t.type === 'BUY' && t.time === bar.time
    );
    const sellTrades = tradeRecords.filter(
      (t) => t.type === 'SELL' && t.time === bar.time
    );

    return {
      time: new Date(bar.time).toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      }),
      fullTime: bar.time,
      close: bar.close,
      high: bar.high,
      low: bar.low,
      buyPrice: buyTrades.length > 0 ? buyTrades[0].price : null,
      sellPrice: sellTrades.length > 0 ? sellTrades[0].price : null,
    };
  });

  // 准备收益曲线数据
  const equityData = equityCurve.map((point, index) => {
    const initialAsset = equityCurve[0].total_asset;
    const gridReturn = ((point.total_asset - initialAsset) / initialAsset) * 100;
    
    const pricePoint = priceCurve[index];
    const holdReturn = pricePoint
      ? ((pricePoint.close - priceCurve[0].close) / priceCurve[0].close) * 100
      : 0;

    return {
      time: new Date(point.time).toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      }),
      gridReturn,
      holdReturn,
      excess: gridReturn - holdReturn,
    };
  });

  const { price_range, current_price } = gridStrategy;

  return (
    <div className="space-y-6">
      {/* 主图：价格走势 + 买卖点 */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-4">价格走势与交易点位</h3>
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={priceData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 12 }}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={['dataMin - 0.1', 'dataMax + 0.1']}
              tick={{ fontSize: 12 }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white p-3 border border-gray-300 rounded shadow">
                      <p className="text-sm font-semibold">{data.fullTime}</p>
                      <p className="text-sm">收盘价: {data.close.toFixed(3)}</p>
                      <p className="text-sm">最高: {data.high.toFixed(3)}</p>
                      <p className="text-sm">最低: {data.low.toFixed(3)}</p>
                      {data.buyPrice && (
                        <p className="text-sm text-red-600">
                          ↑ 买入: {data.buyPrice.toFixed(3)}
                        </p>
                      )}
                      {data.sellPrice && (
                        <p className="text-sm text-blue-600">
                          ↓ 卖出: {data.sellPrice.toFixed(3)}
                        </p>
                      )}
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend />
            
            {/* 价格上下限参考线 */}
            <ReferenceLine
              y={price_range.upper}
              stroke="red"
              strokeDasharray="5 5"
              label="上限"
            />
            <ReferenceLine
              y={price_range.lower}
              stroke="green"
              strokeDasharray="5 5"
              label="下限"
            />
            <ReferenceLine
              y={current_price}
              stroke="gray"
              strokeDasharray="3 3"
              label="基准"
            />

            {/* 收盘价折线 */}
            <Line
              type="monotone"
              dataKey="close"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              name="收盘价"
            />

            {/* 买入点 */}
            <Scatter
              dataKey="buyPrice"
              fill="red"
              shape="triangle"
              name="买入"
            />

            {/* 卖出点 */}
            <Scatter
              dataKey="sellPrice"
              fill="blue"
              shape="triangleDown"
              name="卖出"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* 副图：收益曲线对比 */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-4">收益曲线对比</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={equityData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 12 }}
              interval="preserveStartEnd"
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white p-3 border border-gray-300 rounded shadow">
                      <p className="text-sm font-semibold">{data.time}</p>
                      <p className="text-sm text-blue-600">
                        网格策略: {data.gridReturn.toFixed(2)}%
                      </p>
                      <p className="text-sm text-gray-600">
                        持有不动: {data.holdReturn.toFixed(2)}%
                      </p>
                      <p className="text-sm text-green-600">
                        超额收益: {data.excess.toFixed(2)}%
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend />
            
            {/* 网格策略收益 */}
            <Area
              type="monotone"
              dataKey="gridReturn"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.3}
              name="网格策略"
            />

            {/* 持有不动收益 */}
            <Line
              type="monotone"
              dataKey="holdReturn"
              stroke="#9ca3af"
              strokeDasharray="5 5"
              dot={false}
              name="持有不动"
            />

            {/* 零线 */}
            <ReferenceLine y={0} stroke="#000" strokeDasharray="3 3" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
```

### 任务5：实现交易记录列表（3小时）

#### 5.1 创建TradeList组件
在[`frontend/src/features/analysis/components/backtest/TradeList.jsx`](frontend/src/features/analysis/components/backtest/TradeList.jsx)中：

```javascript
import React, { useState, useMemo } from 'react';
import { formatCurrency } from '@shared/utils/format';

/**
 * 交易记录列表
 */
export default function TradeList({ trades }) {
  const [filter, setFilter] = useState('ALL'); // 'ALL' | 'BUY' | 'SELL'

  const filteredTrades = useMemo(() => {
    if (filter === 'ALL') return trades;
    return trades.filter((t) => t.type === filter);
  }, [trades, filter]);

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">交易记录</h3>
        
        {/* 筛选器 */}
        <div className="flex space-x-2">
          {['ALL', 'BUY', 'SELL'].map((type) => (
            <button
              key={type}
              onClick={() => setFilter(type)}
              className={`px-3 py-1 rounded text-sm ${
                filter === type
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {type === 'ALL' ? '全部' : type === 'BUY' ? '买入' : '卖出'}
            </button>
          ))}
        </div>
      </div>

      {/* 交易表格 */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                时间
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                类型
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                价格
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                数量
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                手续费
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                盈亏
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                持仓
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                资金余额
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredTrades.map((trade, index) => (
              <tr
                key={index}
                className={
                  trade.type === 'BUY'
                    ? 'bg-red-50 hover:bg-red-100'
                    : 'bg-blue-50 hover:bg-blue-100'
                }
              >
                <td className="px-4 py-3 text-sm text-gray-900">
                  {new Date(trade.time).toLocaleString('zh-CN', {
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </td>
                <td className="px-4 py-3 text-sm">
                  <span
                    className={`px-2 py-1 rounded text-xs font-semibold ${
                      trade.type === 'BUY'
                        ? 'bg-red-200 text-red-800'
                        : 'bg-blue-200 text-blue-800'
                    }`}
                  >
                    {trade.type === 'BUY' ? '买入' : '卖出'}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">
                  {trade.price.toFixed(3)}
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">
                  {trade.quantity}股
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-600">
                  {formatCurrency(trade.commission)}
                </td>
                <td className="px-4 py-3 text-sm text-right">
                  {trade.profit !== null ? (
                    <span
                      className={
                        trade.profit > 0
                          ? 'text-red-600 font-semibold'
                          : trade.profit < 0
                          ? 'text-green-600'
                          : 'text-gray-600'
                      }
                    >
                      {trade.profit > 0 ? '+' : ''}
                      {formatCurrency(trade.profit)}
                    </span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">
                  {trade.position}股
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">
                  {formatCurrency(trade.cash)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredTrades.length === 0 && (
        <div className="text-center py-8 text-gray-500">暂无交易记录</div>
      )}
    </div>
  );
}
```

#### 5.2 创建导出文件
在[`frontend/src/features/analysis/components/backtest/index.js`](frontend/src/features/analysis/components/backtest/index.js)中：

```javascript
export { default as BacktestMetrics } from './BacktestMetrics';
export { default as BacktestCharts } from './BacktestCharts';
export { default as TradeList } from './TradeList';
```

### 任务6：集成到分析报告（2小时）

#### 6.1 修改AnalysisReport组件
在[`frontend/src/features/analysis/components/AnalysisReport.jsx`](frontend/src/features/analysis/components/AnalysisReport.jsx)中：

```javascript
import React, { useState } from 'react';
import ReportTabs from './ReportTabs';
import OverviewTab from './OverviewTab';
import BacktestTab from './BacktestTab'; // 新增

export default function AnalysisReport({ etfCode, analysisData }) {
  const [activeTab, setActiveTab] = useState('overview');

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewTab data={analysisData} />;
      case 'suitability':
        return <SuitabilityTab data={analysisData.suitability} />;
      case 'strategy':
        return <StrategyTab data={analysisData.grid_strategy} />;
      case 'backtest':
        return (
          <BacktestTab
            etfCode={etfCode}
            gridStrategy={analysisData.grid_strategy}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <ReportTabs activeTab={activeTab} onTabChange={setActiveTab} />
      <div className="p-6">{renderTabContent()}</div>
    </div>
  );
}
```

### 任务7：编写组件测试（2小时）

#### 7.1 测试BacktestMetrics
在[`frontend/src/features/analysis/components/backtest/__tests__/BacktestMetrics.test.jsx`](frontend/src/features/analysis/components/backtest/__tests__/BacktestMetrics.test.jsx)中：

```javascript
import React from 'react';
import { render, screen } from '@testing-library/react';
import BacktestMetrics from '../BacktestMetrics';

const mockData = {
  metrics: {
    total_return: 0.052,
    annualized_return: 0.385,
    absolute_profit: 520.0,
    max_drawdown: -0.023,
    sharpe_ratio: 1.85,
    volatility: 0.156,
  },
  tradingMetrics: {
    total_trades: 24,
    buy_trades: 12,
    sell_trades: 12,
    win_rate: 0.625,
    profit_loss_ratio: 1.8,
    grid_trigger_rate: 0.452,
  },
  benchmark: {
    hold_return: 0.022,
    excess_return: 0.03,
    excess_return_rate: 1.364,
  },
  period: {
    start_date: '2025-01-10',
    end_date: '2025-01-16',
    trading_days: 5,
    total_bars: 240,
  },
};

describe('BacktestMetrics', () => {
  it('renders core metrics correctly', () => {
    render(<BacktestMetrics {...mockData} />);
    
    expect(screen.getByText('总收益率')).toBeInTheDocument();
    expect(screen.getByText('5.2%')).toBeInTheDocument();
    expect(screen.getByText('年化收益')).toBeInTheDocument();
  });

  it('displays benchmark comparison', () => {
    render(<BacktestMetrics {...mockData} />);
    
    expect(screen.getByText('基准对比')).toBeInTheDocument();
    expect(screen.getByText('持有不动')).toBeInTheDocument();
    expect(screen.getByText('超额收益')).toBeInTheDocument();
  });

  it('shows trading statistics', () => {
    render(<BacktestMetrics {...mockData} />);
    
    expect(screen.getByText('交易统计')).toBeInTheDocument();
    expect(screen.getByText('24次')).toBeInTheDocument();
    expect(screen.getByText('62.5%')).toBeInTheDocument();
  });
});
```

---

## 🔍 阶段实施准则

### 代码质量标准

1. **组件设计**
   - 单一职责，组件功能明确
   - Props类型检查（PropTypes或TypeScript）
   - 合理的组件拆分粒度
   - 可复用性考虑

2. **React最佳实践**
   - 使用函数组件和Hooks
   - 避免不必要的重渲染（useMemo、useCallback）
   - 合理的状态管理
   - 副作用正确处理

3. **样式规范**
   - 使用Tailwind CSS工具类
   - 保持样式一致性
   - 响应式设计
   - 注意无障碍性

4. **图表设计**
   - 数据准确展示
   - 交互体验流畅
   - Tooltip信息完整
   - 颜色语义化

### 开发流程

1. **开发顺序**
   ```
   配置依赖 → 容器组件 → 指标卡片 → 图表组件 → 交易列表 → 集成 → 测试
   ```

2. **提交规范**
   ```
   feat: 添加回测标签页容器组件
   feat: 实现指标卡片展示
   feat: 完成双图表可视化
   feat: 添加交易记录列表
   test: 添加组件单元测试
   style: 优化响应式布局
   ```

3. **组件审查**
   - Props验证完整
   - 边界情况处理
   - 样式响应式
   - 性能优化

### 性能要求

- 首次渲染时间 < 1秒
- 图表渲染流畅（60fps）
- 大数据量优化（虚拟滚动、分页）
- 合理的代码分割

---

## ✅ 成果验收计划

### 功能验收

| 验收项 | 验收标准 | 验收方法 |
|--------|---------|---------|
| 标签页切换 | 正确切换到回测分析标签 | 手动测试 |
| 指标展示 | 所有指标正确显示 | 数据对比验证 |
| 图表渲染 | 价格走势和收益曲线正确 | 视觉检查 |
| 交易点标注 | 买卖点准确标注在图上 | 数据验证 |
| 交易记录 | 列表正确展示和筛选 | 功能测试 |
| 响应式 | 移动端正常显示 | 不同设备测试 |
| 加载状态 | Loading和Error正确处理 | 场景模拟 |

### 质量验收

- ✅ 组件测试覆盖率 ≥ 70%
- ✅ 无控制台错误和警告
- ✅ 响应式适配完成
- ✅ 代码符合ESLint规范
- ✅ 用户体验流畅

### 交付清单

- [ ] [`BacktestTab.jsx`](frontend/src/features/analysis/components/BacktestTab.jsx) - 容器组件
- [ ] [`BacktestMetrics.jsx`](frontend/src/features/analysis/components/backtest/BacktestMetrics.jsx) - 指标卡片
- [ ] [`BacktestCharts.jsx`](frontend/src/features/analysis/components/backtest/BacktestCharts.jsx) - 图表组件
- [ ] [`TradeList.jsx`](frontend/src/features/analysis/components/backtest/TradeList.jsx) - 交易列表
- [ ] 修改的[`ReportTabs.jsx`](frontend/src/features/analysis/components/ReportTabs.jsx)
- [ ] 修改的[`AnalysisReport.jsx`](frontend/src/features/analysis/components/AnalysisReport.jsx)
- [ ] API服务扩展
- [ ] 组件测试文件

### 验收方式

1. **功能测试**
   - 切换到回测标签，验证加载流程
   - 检查各项指标数值正确性
   - 验证图表数据准确性
   - 测试交易记录筛选功能

2. **视觉验证**
   - 检查UI布局合理性
   - 验证颜色和样式一致性
   - 测试不同屏幕尺寸表现
   - 确认交互反馈清晰

3. **单元测试**
   ```bash
   npm test -- BacktestMetrics
   npm test -- BacktestCharts
   npm test -- TradeList
   ```

4. **性能测试**
   - 使用Chrome DevTools Performance分析
   - 检查组件渲染次数
   - 验证大数据量表现

---

## 📌 注意事项

1. **图表性能**
   - 超过500个数据点考虑抽样
   - 使用ResponsiveContainer自适应
   - 合理设置refresh频率

2. **数据格式**
   - 时间格式统一处理
   - 数值精度控制
   - 空值和异常值处理

3. **用户体验**
   - Loading状态清晰
   - 错误提示友好
   - 空状态处理
   - 操作反馈及时

4. **移动端适配**
   - 图表触摸交互
   - 表格横向滚动
   - 按钮点击区域
   - 字体大小合理

5. **浏览器兼容**
   - 测试主流浏览器
   - Polyfill必要API
   - CSS前缀处理

---

## 🔗 与其他阶段的衔接

### 前置阶段提供

**阶段2交付**：
- ✅ `/api/grid/backtest` API接口
- ✅ 标准化JSON响应
- ✅ 完整的回测数据

### 本阶段交付给阶段4

- ✅ 基础回测组件
- ✅ 图表可视化
- ✅ 交易记录展示
- ✅ API集成逻辑

### 阶段4需要实现

- 网格表现分析（GridPerformance）
- 参数编辑功能
- 导出功能
- 完整的集成测试
- 性能优化
- 用户体验完善

---

**文档版本**：v1.0  
**创建时间**：2025-01-10  
**预计工时**：18小时  
**负责团队**：前端开发组
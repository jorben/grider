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
    "backtest_period": {
      "start_date": "2025-01-10",
      "end_date": "2025-01-16",
      "trading_days": 5,
      "total_bars": 240
    },
    "performance_metrics": {
      "total_return": 0.052,
      "annualized_return": 0.385,
      "absolute_profit": 520.00,
      "max_drawdown": -0.023,
      "sharpe_ratio": 1.85,
      "volatility": 0.156
    },
    "trading_metrics": {
      "total_trades": 24,
      "buy_trades": 12,
      "sell_trades": 12,
      "win_rate": 0.625,
      "profit_loss_ratio": 1.8,
      "grid_trigger_rate": 0.452
    },
    "benchmark_comparison": {
      "hold_return": 0.022,
      "excess_return": 0.030,
      "excess_return_rate": 1.364
    },
    "equity_curve": [
      {
        "time": "2025-01-10 09:30:00",
        "total_asset": 10000.00
      }
    ],
    "price_curve": [
      {
        "time": "2025-01-10 09:30:00",
        "open": 3.500,
        "high": 3.510,
        "low": 3.495,
        "close": 3.505,
        "volume": 12500
      }
    ],
    "trade_records": [
      {
        "time": "2025-01-10 10:05:00",
        "type": "BUY",
        "price": 3.470,
        "quantity": 100,
        "commission": 0.35,
        "profit": null,
        "position": 800,
        "cash": 9649.65
      }
    ],
    "final_state": {
      "cash": 10520.00,
      "position": 700,
      "total_asset": 12970.00
    }
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

## 数据结构说明

### 性能指标 (performance_metrics)

| 字段 | 类型 | 说明 |
|------|------|------|
| total_return | float | 总收益率 |
| annualized_return | float | 年化收益率 |
| absolute_profit | float | 绝对收益 |
| max_drawdown | float | 最大回撤 |
| sharpe_ratio | float/null | 夏普比率 |
| volatility | float | 波动率 |

### 交易指标 (trading_metrics)

| 字段 | 类型 | 说明 |
|------|------|------|
| total_trades | int | 总交易次数 |
| buy_trades | int | 买入次数 |
| sell_trades | int | 卖出次数 |
| win_rate | float | 胜率 |
| profit_loss_ratio | float/null | 盈亏比 |
| grid_trigger_rate | float | 网格触发率 |

### 基准对比 (benchmark_comparison)

| 字段 | 类型 | 说明 |
|------|------|------|
| hold_return | float | 持有不动收益率 |
| excess_return | float | 超额收益 |
| excess_return_rate | float | 超额收益率 |

### 交易记录 (trade_records)

| 字段 | 类型 | 说明 |
|------|------|------|
| time | string | 交易时间 |
| type | string | 交易类型 (BUY/SELL) |
| price | float | 交易价格 |
| quantity | int | 交易数量 |
| commission | float | 手续费 |
| profit | float/null | 盈亏 |
| position | int | 持仓数量 |
| cash | float | 可用资金 |

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 400 | 参数验证失败 |
| 500 | 服务器内部错误 |

## 使用示例

```javascript
// 前端调用示例
const response = await fetch('/api/grid/backtest', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    etfCode: '510300',
    gridStrategy: {
      current_price: 3.500,
      price_range: { lower: 3.200, upper: 3.800 },
      grid_config: {
        count: 20,
        type: '等差',
        step_size: 0.030,
        single_trade_quantity: 100
      },
      fund_allocation: {
        base_position_amount: 2500.00,
        base_position_shares: 700,
        grid_trading_amount: 7000.00
      }
    },
    backtestConfig: {
      commissionRate: 0.0002,
      minCommission: 5.0,
      riskFreeRate: 0.03,
      tradingDaysPerYear: 244
    }
  })
});

const result = await response.json();
if (result.success) {
  console.log('回测成功:', result.data);
} else {
  console.error('回测失败:', result.error);
}
```

---

**文档版本**: v1.0
**最后更新**: 2025-01-10
**维护者**: 后端服务组
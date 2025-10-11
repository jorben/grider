import React from 'react';
import { formatPercent } from '@shared/utils/format';

/**
 * 回测指标卡片
 */
export default function BacktestMetrics({ metrics = {}, tradingMetrics = {}, benchmark = {}, period = {} }) {
  const coreMetrics = [
    {
      label: '总收益率',
      value: formatPercent(metrics.total_return),
      color: (metrics.total_return ?? 0) >= 0 ? 'text-green-600' : 'text-red-600',
      extra: `超额${formatPercent(benchmark.excess_return)}`,
      extraColor: (benchmark.excess_return ?? 0) >= 0 ? 'text-green-500' : 'text-red-500',
    },
    {
      label: '年化收益',
      value: formatPercent(metrics.annualized_return),
      color: (metrics.annualized_return ?? 0) >= 0 ? 'text-green-600' : 'text-red-600',
    },
    {
      label: '最大回撤',
      value: formatPercent(metrics.max_drawdown),
      color: 'text-red-600',
    },
    {
      label: '夏普比率',
      value: metrics.sharpe_ratio != null ? metrics.sharpe_ratio.toFixed(2) : 'N/A',
      color: 'text-blue-600',
    },
  ];

  const tradingMetricsData = [
    {
      label: '交易次数',
      value: `${tradingMetrics.total_trades ?? 0}次`,
    },
    {
      label: '胜率',
      value: formatPercent(tradingMetrics.win_rate),
      color: (tradingMetrics.win_rate ?? 0) >= 0.5 ? 'text-green-600' : 'text-gray-600',
    },
    {
      label: '盈亏比',
      value: tradingMetrics.profit_loss_ratio != null
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
              (benchmark.excess_return ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatPercent(benchmark.excess_return)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
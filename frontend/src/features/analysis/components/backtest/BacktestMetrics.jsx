import React from 'react';
import { formatPercent } from '@shared/utils/format';
import { TrendingUp, BarChart3, Activity, Target, Calendar, DollarSign, Percent, TrendingDown } from 'lucide-react';

/**
 * 回测指标卡片
 */
export default function BacktestMetrics({ metrics = {}, tradingMetrics = {}, benchmark = {}, period = {} }) {
  const coreMetrics = [
    {
      label: '区间收益率',
      value: formatPercent(metrics.total_return),
      color: (metrics.total_return ?? 0) >= 0 ? 'text-red-600' : 'text-green-600',
      icon: TrendingUp,
      bgColor: (metrics.total_return ?? 0) >= 0 ? 'bg-red-100' : 'bg-green-100',
      extra: `超额${formatPercent(benchmark.excess_return)}`,
      extraColor: (benchmark.excess_return ?? 0) >= 0 ? 'text-red-500' : 'text-green-500',
    },
    {
      label: '最大回撤',
      value: formatPercent(metrics.max_drawdown),
      color: 'text-green-600',
      icon: TrendingDown,
      bgColor: 'bg-green-100',
    },
    {
      label: '夏普比率',
      value: metrics.sharpe_ratio != null ? metrics.sharpe_ratio.toFixed(2) : 'N/A',
      color: 'text-grey-600',
      icon: BarChart3,
      bgColor: 'bg-grey-100',
    },
    {
      label: '年化收益',
      value: formatPercent(metrics.annualized_return),
      color: (metrics.annualized_return ?? 0) >= 0 ? 'text-red-600' : 'text-green-600',
      icon: TrendingUp,
      bgColor: (metrics.annualized_return ?? 0) >= 0 ? 'bg-red-100' : 'bg-green-100',
    },
  ];

  const tradingMetricsData = [
    {
      label: '交易次数',
      value: `${tradingMetrics.total_trades ?? 0}次`,
      icon: Activity,
      bgColor: 'bg-purple-100',
      color: 'text-purple-600',
    },
    {
      label: '胜率',
      value: formatPercent(tradingMetrics.win_rate),
      color: (tradingMetrics.win_rate ?? 0) >= 0.5 ? 'text-red-600' : 'text-gray-600',
      icon: Target,
      bgColor: (tradingMetrics.win_rate ?? 0) >= 0.5 ? 'bg-red-100' : 'bg-gray-100',
    },
    {
      label: '盈亏比',
      value: tradingMetrics.profit_loss_ratio != null
        ? tradingMetrics.profit_loss_ratio.toFixed(2)
        : 'N/A',
      icon: DollarSign,
      bgColor: 'bg-orange-100',
      color: 'text-orange-600',
    },
    {
      label: '网格触发率',
      value: formatPercent(tradingMetrics.grid_trigger_rate),
      icon: Percent,
      bgColor: 'bg-indigo-100',
      color: 'text-indigo-600',
    },
  ];

  return (
    <div className="space-y-6">
      {/* 回测周期 */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Calendar className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <p className="text-sm font-medium text-blue-800">回测区间</p>
            <p className="text-sm text-blue-700">
              {period.start_date} ~ {period.end_date}
              （{period.trading_days}个交易日，{period.total_bars}组数据点）
            </p>
          </div>
        </div>
      </div>

      {/* 核心指标 */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-gradient-to-r from-green-100 to-blue-100 rounded-lg">
            <TrendingUp className="w-5 h-5 text-gradient-to-r from-green-600 to-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">核心指标</h3>
            <p className="text-sm text-gray-600">策略表现的关键评估指标</p>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          {coreMetrics.map((metric, index) => {
            const Icon = metric.icon;
            return (
              <div key={index} className="text-center p-4 bg-gray-50 rounded-lg">
                <div className={`flex items-center justify-center w-10 h-10 mx-auto mb-2 ${metric.bgColor} rounded-full`}>
                  <Icon className={`w-5 h-5 ${metric.color}`} />
                </div>
                <p className="text-sm text-gray-600 mb-1">{metric.label}</p>
                <p className={`text-xl font-bold ${metric.color}`}>{metric.value}</p>
                {metric.extra && (
                  <p className={`text-xs mt-1 ${metric.extraColor}`}>▲ {metric.extra}</p>
                )}
              </div>
            );
          })}
        </div>

        {/* 基准对比 */}

        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-gradient-to-r from-green-100 to-blue-100 rounded-lg">
            <BarChart3 className="w-5 h-5 text-gradient-to-r from-gray-600 to-green-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">基准对比</h3>
            <p className="text-sm text-gray-600">与持有不动策略的收益对比</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-center w-10 h-10 mx-auto mb-2 bg-gray-100 rounded-full">
              <TrendingUp className="w-5 h-5 text-gray-600" />
            </div>
            <p className="text-sm text-gray-600 mb-1">网格策略</p>
            <p className="text-lg font-bold text-gray-600">
              {formatPercent(metrics.total_return)}
            </p>
          </div>
          <div className="text-center p-4 bg-gradient-to-r from-green-50 to-red-50 rounded-lg">
            <div className={`flex items-center justify-center w-10 h-10 mx-auto mb-2 ${
              (benchmark.excess_return ?? 0) >= 0 ? 'bg-red-100' : 'bg-green-100'
            } rounded-full`}>
              <Target className={`w-5 h-5 ${
                (benchmark.excess_return ?? 0) >= 0 ? 'text-red-600' : 'text-green-600'
              }`} />
            </div>
            <p className="text-sm text-gray-600 mb-1">超额收益</p>
            <p className={`text-lg font-bold ${
              (benchmark.excess_return ?? 0) >= 0 ? 'text-red-600' : 'text-green-600'
            }`}>
              {formatPercent(benchmark.excess_return)}
            </p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-center w-10 h-10 mx-auto mb-2 bg-gray-100 rounded-full">
              <Calendar className="w-5 h-5 text-gray-600" />
            </div>
            <p className="text-sm text-gray-600 mb-1">持有不动</p>
            <p className="text-lg font-bold text-gray-700">
              {formatPercent(benchmark.hold_return)}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-gradient-to-r from-purple-100 to-indigo-100 rounded-lg">
            <Activity className="w-5 h-5 text-gradient-to-r from-purple-600 to-indigo-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">交易统计</h3>
            <p className="text-sm text-gray-600">网格交易的执行情况分析</p>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {tradingMetricsData.map((metric, index) => {
            const Icon = metric.icon;
            return (
              <div key={index} className="text-center p-4 bg-gray-50 rounded-lg">
                <div className={`flex items-center justify-center w-10 h-10 mx-auto mb-2 ${metric.bgColor} rounded-full`}>
                  <Icon className={`w-5 h-5 ${metric.color || 'text-gray-600'}`} />
                </div>
                <p className="text-sm text-gray-600 mb-1">{metric.label}</p>
                <p className={`text-xl font-semibold ${metric.color || 'text-gray-800'}`}>
                  {metric.value}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
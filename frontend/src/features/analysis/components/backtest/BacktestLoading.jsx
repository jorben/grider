import React from 'react';

/**
 * 回测加载状态组件
 */
export default function BacktestLoading({ stage = 'loading' }) {
  const stages = {
    loading: '正在准备回测数据...',
    fetching: '获取历史K线数据...',
    calculating: '执行回测计算...',
    analyzing: '生成分析报告...',
  };

  return (
    <div className="flex flex-col items-center justify-center py-16">
      {/* 加载动画 */}
      <div className="relative">
        <div className="w-20 h-20 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl">📊</span>
        </div>
      </div>

      {/* 状态文字 */}
      <p className="mt-6 text-lg text-gray-700 font-medium">{stages[stage]}</p>

      {/* 进度提示 */}
      <div className="mt-4 space-y-2 text-sm text-gray-500">
        <p>✓ 获取交易日历</p>
        <p className={stage !== 'loading' ? 'text-gray-900' : ''}>
          {stage !== 'loading' ? '✓' : '○'} 加载K线数据
        </p>
        <p className={stage === 'calculating' || stage === 'analyzing' ? 'text-gray-900' : ''}>
          {stage === 'calculating' || stage === 'analyzing' ? '✓' : '○'} 执行回测
        </p>
        <p className={stage === 'analyzing' ? 'text-gray-900' : ''}>
          {stage === 'analyzing' ? '✓' : '○'} 生成报告
        </p>
      </div>
    </div>
  );
}
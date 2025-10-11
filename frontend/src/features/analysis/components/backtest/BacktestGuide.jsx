import React, { useState } from 'react';
import { usePersistedState } from '@shared/hooks';

/**
 * 回测功能引导组件
 */
export default function BacktestGuide() {
  const [showGuide, setShowGuide] = usePersistedState('backtest-guide-shown', true);

  if (!showGuide) return null;

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <span className="text-2xl">💡</span>
        </div>
        <div className="ml-3 flex-1">
          <h4 className="text-sm font-semibold text-blue-900 mb-2">
            回测分析功能说明
          </h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• 基于最近5个交易日的5分钟K线数据进行模拟回测</li>
            <li>• 严格按照网格策略参数执行交易逻辑</li>
            <li>• 可调整手续费率等参数查看不同情况下的表现</li>
            <li>• 回测结果仅供参考，不构成投资建议</li>
          </ul>
        </div>
        <button
          onClick={() => setShowGuide(false)}
          className="flex-shrink-0 ml-3 text-blue-600 hover:text-blue-800"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
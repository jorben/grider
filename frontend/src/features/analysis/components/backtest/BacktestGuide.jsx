import React, { useState } from 'react';
import { usePersistedState } from '@shared/hooks';
import { Lightbulb, X, BarChart3, Settings, AlertTriangle } from 'lucide-react';

/**
 * 回测功能引导组件
 */
export default function BacktestGuide() {
  const [showGuide, setShowGuide] = usePersistedState('backtest-guide-shown', true);

  if (!showGuide) return null;

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6 mb-6">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0">
          <div className="p-2 bg-gradient-to-r from-blue-100 to-indigo-100 rounded-lg">
            <Lightbulb className="w-5 h-5 text-gradient-to-r from-blue-600 to-indigo-600" />
          </div>
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-blue-900">
              回测分析功能说明
            </h4>
            <button
              onClick={() => setShowGuide(false)}
              className="flex-shrink-0 text-blue-600 hover:text-blue-800 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="flex items-start gap-2">
              <BarChart3 className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <span className="text-blue-800">基于最近30个交易日的5分钟K线数据进行模拟回测</span>
            </div>
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-orange-600 mt-0.5 flex-shrink-0" />
              <span className="text-blue-800">由于非基于逐笔K线，成交价格采用K线均值</span>
            </div>
            <div className="flex items-start gap-2">
              <Settings className="w-4 h-4 text-purple-600 mt-0.5 flex-shrink-0" />
              <span className="text-blue-800">可调整手续费率等参数查看不同情况下的表现</span>
            </div>
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-orange-600 mt-0.5 flex-shrink-0" />
              <span className="text-blue-800">回测结果仅供参考，不构成投资建议</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
import React from 'react';
import { BarChart3, Calendar, Database, Calculator, FileText } from 'lucide-react';

/**
 * 回测加载状态组件
 */
export default function BacktestLoading({ stage = 'loading' }) {
  const stages = {
    loading: {
      title: '正在准备回测数据...',
      icon: Calendar,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    fetching: {
      title: '获取历史K线数据...',
      icon: Database,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    calculating: {
      title: '执行回测计算...',
      icon: Calculator,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    analyzing: {
      title: '生成分析报告...',
      icon: FileText,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
    },
  };

  const currentStage = stages[stage];
  const Icon = currentStage.icon;

  const progressSteps = [
    { key: 'calendar', label: '获取交易日历', completed: stage !== 'loading' },
    { key: 'data', label: '加载K线数据', completed: stage === 'fetching' || stage === 'calculating' || stage === 'analyzing' },
    { key: 'calculation', label: '执行回测', completed: stage === 'calculating' || stage === 'analyzing' },
    { key: 'report', label: '生成报告', completed: stage === 'analyzing' },
  ];

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-8">
      <div className="flex flex-col items-center justify-center">
        {/* 加载动画 */}
        <div className="relative mb-6">
          <div className="w-20 h-20 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className={`p-3 ${currentStage.bgColor} rounded-full`}>
              <Icon className={`w-8 h-8 ${currentStage.color}`} />
            </div>
          </div>
        </div>

        {/* 状态文字 */}
        <div className="text-center mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {currentStage.title}
          </h3>
          <p className="text-sm text-gray-600">基于ATR算法进行智能回测分析，请稍候...</p>
        </div>

        {/* 进度提示 */}
        <div className="w-full max-w-md space-y-3">
          {progressSteps.map((step, index) => {
            const StepIcon = step.completed ? BarChart3 : Calendar;
            return (
              <div
                key={step.key}
                className={`flex items-center gap-3 p-3 rounded-lg transition-all duration-300 ${
                  step.completed
                    ? 'bg-green-50 border border-green-200'
                    : 'bg-gray-50 border border-gray-200'
                }`}
              >
                <div
                  className={`p-2 rounded-lg ${
                    step.completed ? 'bg-green-200' : 'bg-gray-200'
                  }`}
                >
                  <StepIcon
                    className={`w-4 h-4 ${
                      step.completed ? 'text-green-700' : 'text-gray-500'
                    }`}
                  />
                </div>
                <div className="flex-1">
                  <p
                    className={`text-sm font-medium ${
                      step.completed ? 'text-green-900' : 'text-gray-600'
                    }`}
                  >
                    {step.label}
                  </p>
                </div>
                {step.completed && (
                  <div className="w-4 h-4 bg-green-600 rounded-full flex items-center justify-center">
                    <svg
                      className="w-2 h-2 text-white"
                      fill="currentColor"
                      viewBox="0 0 8 8"
                    >
                      <path d="M6.564.75l-3.59 3.612-1.538-1.55L0 4.26l2.974 2.99L8 2.193z" />
                    </svg>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
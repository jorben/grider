import React from 'react';
import { AlertTriangle, RefreshCw, Wifi, Settings } from 'lucide-react';

/**
 * 回测错误状态组件
 */
export default function BacktestError({ error, onRetry }) {
  const getErrorInfo = (errorMessage) => {
    if (errorMessage.includes('K线数据')) {
      return {
        icon: Wifi,
        title: '数据获取失败',
        description: '无法获取历史K线数据，可能是网络问题或数据源暂时不可用',
        suggestions: ['检查网络连接', '稍后重试', '选择其他时间范围'],
        color: 'text-orange-600',
        bgColor: 'bg-orange-100',
      };
    }

    if (errorMessage.includes('参数')) {
      return {
        icon: Settings,
        title: '参数错误',
        description: '回测参数不正确，请检查网格策略配置',
        suggestions: ['返回策略页面重新生成', '检查参数值是否合理'],
        color: 'text-red-600',
        bgColor: 'bg-red-100',
      };
    }

    return {
      icon: AlertTriangle,
      title: '回测失败',
      description: errorMessage,
      suggestions: ['稍后重试', '刷新页面', '联系技术支持'],
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    };
  };

  const errorInfo = getErrorInfo(error);
  const Icon = errorInfo.icon;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-8">
      <div className="text-center">
        <div className={`flex items-center justify-center w-20 h-20 mx-auto mb-4 ${errorInfo.bgColor} rounded-full`}>
          <Icon className={`w-10 h-10 ${errorInfo.color}`} />
        </div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          {errorInfo.title}
        </h3>
        <p className="text-gray-600 mb-6">{errorInfo.description}</p>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-yellow-600" />
            <p className="text-sm font-medium text-yellow-800">建议操作</p>
          </div>
          <ul className="text-sm text-yellow-700 space-y-1">
            {errorInfo.suggestions.map((suggestion, index) => (
              <li key={index} className="flex items-center gap-2">
                <span className="w-1 h-1 bg-yellow-600 rounded-full"></span>
                {suggestion}
              </li>
            ))}
          </ul>
        </div>

        <button
          onClick={onRetry}
          className="btn btn-primary"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          重新回测
        </button>
      </div>
    </div>
  );
}
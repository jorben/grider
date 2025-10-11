import React from 'react';

/**
 * 回测错误状态组件
 */
export default function BacktestError({ error, onRetry }) {
  const getErrorInfo = (errorMessage) => {
    if (errorMessage.includes('K线数据')) {
      return {
        icon: '📡',
        title: '数据获取失败',
        description: '无法获取历史K线数据，可能是网络问题或数据源暂时不可用',
        suggestions: ['检查网络连接', '稍后重试', '选择其他时间范围'],
      };
    }

    if (errorMessage.includes('参数')) {
      return {
        icon: '⚙️',
        title: '参数错误',
        description: '回测参数不正确，请检查网格策略配置',
        suggestions: ['返回策略页面重新生成', '检查参数值是否合理'],
      };
    }

    return {
      icon: '❌',
      title: '回测失败',
      description: errorMessage,
      suggestions: ['稍后重试', '刷新页面', '联系技术支持'],
    };
  };

  const errorInfo = getErrorInfo(error);

  return (
    <div className="bg-white rounded-lg shadow p-8">
      <div className="text-center">
        <div className="text-6xl mb-4">{errorInfo.icon}</div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          {errorInfo.title}
        </h3>
        <p className="text-gray-600 mb-6">{errorInfo.description}</p>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <p className="text-sm font-medium text-yellow-800 mb-2">💡 建议操作：</p>
          <ul className="text-sm text-yellow-700 space-y-1">
            {errorInfo.suggestions.map((suggestion, index) => (
              <li key={index}>• {suggestion}</li>
            ))}
          </ul>
        </div>

        <button
          onClick={onRetry}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          🔄 重新回测
        </button>
      </div>
    </div>
  );
}
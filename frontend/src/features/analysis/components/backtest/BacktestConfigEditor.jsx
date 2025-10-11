import React, { useState } from 'react';

/**
 * 回测参数编辑器
 */
export default function BacktestConfigEditor({ config, onConfigChange, onRunBacktest }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedConfig, setEditedConfig] = useState(config);

  const handleInputChange = (field, value) => {
    setEditedConfig({
      ...editedConfig,
      [field]: parseFloat(value),
    });
  };

  const handleSave = () => {
    onConfigChange(editedConfig);
    setIsEditing(false);
    onRunBacktest();
  };

  const handleReset = () => {
    const defaultConfig = {
      commissionRate: 0.0002,
      minCommission: 5.0,
      riskFreeRate: 0.03,
      tradingDaysPerYear: 244,
    };
    setEditedConfig(defaultConfig);
    onConfigChange(defaultConfig);
  };

  if (!isEditing) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">回测参数</h3>
          <button
            onClick={() => setIsEditing(true)}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            ⚙️ 编辑参数
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 bg-gray-50 rounded">
            <p className="text-sm text-gray-600">手续费率</p>
            <p className="text-lg font-semibold">{(config.commissionRate * 100).toFixed(3)}%</p>
          </div>
          <div className="p-3 bg-gray-50 rounded">
            <p className="text-sm text-gray-600">最低收费</p>
            <p className="text-lg font-semibold">¥{config.minCommission}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded">
            <p className="text-sm text-gray-600">无风险利率</p>
            <p className="text-lg font-semibold">{(config.riskFreeRate * 100).toFixed(1)}%</p>
          </div>
          <div className="p-3 bg-gray-50 rounded">
            <p className="text-sm text-gray-600">年交易日数</p>
            <p className="text-lg font-semibold">{config.tradingDaysPerYear}天</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold mb-4">编辑回测参数</h3>

      <div className="space-y-4">
        {/* 手续费率 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            手续费率 (%)
            <span className="ml-2 text-xs text-gray-500">默认0.02%</span>
          </label>
          <input
            type="number"
            step="0.001"
            value={(editedConfig.commissionRate * 100).toFixed(3)}
            onChange={(e) => handleInputChange('commissionRate', parseFloat(e.target.value) / 100)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* 最低收费 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            最低收费 (元)
            <span className="ml-2 text-xs text-gray-500">默认5元</span>
          </label>
          <input
            type="number"
            step="1"
            value={editedConfig.minCommission}
            onChange={(e) => handleInputChange('minCommission', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* 无风险利率 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            无风险利率 (%)
            <span className="ml-2 text-xs text-gray-500">默认3%</span>
          </label>
          <input
            type="number"
            step="0.1"
            value={(editedConfig.riskFreeRate * 100).toFixed(1)}
            onChange={(e) => handleInputChange('riskFreeRate', parseFloat(e.target.value) / 100)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* 年交易日数 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            年交易日数
            <span className="ml-2 text-xs text-gray-500">默认244天</span>
          </label>
          <input
            type="number"
            step="1"
            value={editedConfig.tradingDaysPerYear}
            onChange={(e) => handleInputChange('tradingDaysPerYear', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* 操作按钮 */}
        <div className="flex space-x-3 pt-3">
          <button
            onClick={handleSave}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            保存并重新回测
          </button>
          <button
            onClick={handleReset}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
          >
            重置
          </button>
          <button
            onClick={() => setIsEditing(false)}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
          >
            取消
          </button>
        </div>
      </div>
    </div>
  );
}
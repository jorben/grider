import React, { useState } from 'react';
import { Settings, Calculator, DollarSign, Percent, Calendar } from 'lucide-react';

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
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Settings className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">回测参数设置</h3>
            <p className="text-sm text-gray-600">手续费、无风险利率等参数配置</p>
          </div>
          <button
            onClick={() => setIsEditing(true)}
            className="ml-auto btn btn-secondary"
          >
            <Settings className="w-4 h-4 mr-2" />
            编辑参数
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-center w-8 h-8 mx-auto mb-2 bg-blue-100 rounded-full">
              <Percent className="w-4 h-4 text-blue-600" />
            </div>
            <p className="text-sm text-gray-600 mb-1">手续费率</p>
            <p className="text-lg font-bold text-gray-900">{(config.commissionRate * 100).toFixed(3)}%</p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-center w-8 h-8 mx-auto mb-2 bg-green-100 rounded-full">
              <DollarSign className="w-4 h-4 text-green-600" />
            </div>
            <p className="text-sm text-gray-600 mb-1">最低收费</p>
            <p className="text-lg font-bold text-gray-900">¥{config.minCommission}</p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-center w-8 h-8 mx-auto mb-2 bg-purple-100 rounded-full">
              <Calculator className="w-4 h-4 text-purple-600" />
            </div>
            <p className="text-sm text-gray-600 mb-1">无风险利率</p>
            <p className="text-lg font-bold text-gray-900">{(config.riskFreeRate * 100).toFixed(1)}%</p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-center w-8 h-8 mx-auto mb-2 bg-orange-100 rounded-full">
              <Calendar className="w-4 h-4 text-orange-600" />
            </div>
            <p className="text-sm text-gray-600 mb-1">年交易日数</p>
            <p className="text-lg font-bold text-gray-900">{config.tradingDaysPerYear}天</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-blue-100 rounded-lg">
          <Settings className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">编辑回测参数</h3>
          <p className="text-sm text-gray-600">调整手续费、无风险利率等参数</p>
        </div>
      </div>

      <div className="space-y-6">
        {/* 手续费率 */}
        <div>
          <label className="label">
            <div className="flex items-center gap-2">
              <Percent className="w-4 h-4 text-blue-600" />
              手续费率 (%)
            </div>
            <span className="text-xs text-gray-500 font-normal">默认0.02%</span>
          </label>
          <input
            type="number"
            step="0.001"
            value={(editedConfig.commissionRate * 100).toFixed(3)}
            onChange={(e) => handleInputChange('commissionRate', parseFloat(e.target.value) / 100)}
            className="input"
          />
        </div>

        {/* 最低收费 */}
        <div>
          <label className="label">
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-green-600" />
              最低收费 (元)
            </div>
            <span className="text-xs text-gray-500 font-normal">默认5元</span>
          </label>
          <input
            type="number"
            step="1"
            value={editedConfig.minCommission}
            onChange={(e) => handleInputChange('minCommission', e.target.value)}
            className="input"
          />
        </div>

        {/* 无风险利率 */}
        <div>
          <label className="label">
            <div className="flex items-center gap-2">
              <Calculator className="w-4 h-4 text-purple-600" />
              无风险利率 (%)
            </div>
            <span className="text-xs text-gray-500 font-normal">默认3%</span>
          </label>
          <input
            type="number"
            step="0.1"
            value={(editedConfig.riskFreeRate * 100).toFixed(1)}
            onChange={(e) => handleInputChange('riskFreeRate', parseFloat(e.target.value) / 100)}
            className="input"
          />
        </div>

        {/* 年交易日数 */}
        <div>
          <label className="label">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-orange-600" />
              年交易日数
            </div>
            <span className="text-xs text-gray-500 font-normal">默认244天</span>
          </label>
          <input
            type="number"
            step="1"
            value={editedConfig.tradingDaysPerYear}
            onChange={(e) => handleInputChange('tradingDaysPerYear', e.target.value)}
            className="input"
          />
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-3 pt-4">
          <button
            onClick={handleSave}
            className="btn btn-primary flex-1"
          >
            保存并重新回测
          </button>
          <button
            onClick={handleReset}
            className="btn btn-secondary"
          >
            重置
          </button>
          <button
            onClick={() => setIsEditing(false)}
            className="btn btn-secondary"
          >
            取消
          </button>
        </div>
      </div>
    </div>
  );
}
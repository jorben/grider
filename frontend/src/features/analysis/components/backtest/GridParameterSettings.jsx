import React, { useState, useEffect } from 'react';
import { Settings, TrendingUp, DollarSign, Target, Hash, Calendar, AlertTriangle, CheckCircle, Percent, Calculator } from 'lucide-react';

/**
 * 网格参数设置
 * 统一的网格参数和回测参数设置面板
 */
export default function GridParameterSettings({
  gridStrategy,
  inputParameters,
  defaultDates,
  backtestConfig,
  onConfigChange,
  onParametersChange,
  onRunBacktest,
  isVisible = true
}) {
  const [isEditingGrid, setIsEditingGrid] = useState(false);
  const [isEditingCommission, setIsEditingCommission] = useState(false);
  const [editedGridParams, setEditedGridParams] = useState({});
  const [editedCommissionConfig, setEditedCommissionConfig] = useState(backtestConfig);
  const [validationErrors, setValidationErrors] = useState({});
  const [isValid, setIsValid] = useState(true);

  // 初始化网格参数
  useEffect(() => {
    if (gridStrategy && inputParameters) {
      const initialParams = {
        // 价格区间参数
        priceLower: gridStrategy.price_range?.lower || 0,
        priceUpper: gridStrategy.price_range?.upper || 0,
        // 投资金额参数
        totalCapital: inputParameters.total_capital || inputParameters.totalCapital || 0,
        // 基准价格参数
        benchmarkPrice: gridStrategy.current_price || 0,
        // 网格步长参数 - 等比网格显示为百分比
        gridStepSize: gridStrategy.grid_config?.type?.includes('等比')
          ? (gridStrategy.grid_config?.step_ratio || 0) * 100
          : (gridStrategy.grid_config?.step_size || 0),
        // 单笔数量参数
        singleTradeQuantity: gridStrategy.grid_config?.single_trade_quantity || 0,
        // 回测区间参数 (使用默认值，可自定义)
        startDate: defaultDates?.start_date || '',
        endDate: defaultDates?.end_date || ''
      };
      setEditedGridParams(initialParams);
      setValidationErrors({});
    }
  }, [gridStrategy, inputParameters, defaultDates]);

  // 初始化手续费配置
  useEffect(() => {
    setEditedCommissionConfig(backtestConfig);
  }, [backtestConfig]);

  // 网格参数验证
  const validateGridParameters = (params) => {
    const errors = {};

    // 价格区间验证
    if (params.priceUpper <= params.priceLower) {
      errors.priceRange = '价格上限必须大于下限';
    }
    if (params.priceLower <= 0 || params.priceUpper <= 0) {
      errors.priceRange = '价格必须大于0';
    }
    if (params.benchmarkPrice < params.priceLower || params.benchmarkPrice > params.priceUpper) {
      errors.benchmarkPrice = '基准价格必须在价格区间内';
    }

    // 价格区间合理性检查
    const priceRangeRatio = (params.priceUpper - params.priceLower) / params.benchmarkPrice;
    if (priceRangeRatio < 0.05) {
      errors.priceRange = '价格区间过小（建议至少5%）';
    }
    if (priceRangeRatio > 1.0) {
      errors.priceRange = '价格区间过大（建议不超过100%）';
    }

    // 投资金额验证
    if (params.totalCapital < 1000) {
      errors.totalCapital = '投资金额至少1000元';
    }
    if (params.totalCapital > 10000000) {
      errors.totalCapital = '投资金额不能超过1000万元';
    }

    // 网格步长验证
    if (params.gridStepSize <= 0) {
      errors.gridStepSize = '网格步长必须大于0';
    }

    // 根据网格类型计算实际步长值进行验证
    let actualStepSize = params.gridStepSize;
    if (gridStrategy?.grid_config?.type?.includes('等比')) {
      // 等比网格：gridStepSize是百分比，需要转换为实际价格差
      actualStepSize = params.benchmarkPrice * (params.gridStepSize / 100);
    }
    // 等差网格：gridStepSize就是实际价格差

    if (actualStepSize > (params.priceUpper - params.priceLower) / 2) {
      errors.gridStepSize = '网格步长过大，请适当缩小';
    }

    // 单笔数量验证
    if (params.singleTradeQuantity <= 0) {
      errors.singleTradeQuantity = '单笔数量必须大于0';
    }
    if (params.totalCapital > 0 && params.singleTradeQuantity * params.benchmarkPrice > params.totalCapital) {
      errors.singleTradeQuantity = '单笔交易金额不能超过总投资金额';
    }

    // 日期验证
    if (params.startDate && params.endDate) {
      const start = new Date(params.startDate);
      const end = new Date(params.endDate);
      if (start >= end) {
        errors.dates = '开始日期必须早于结束日期';
      }
      const daysDiff = (end - start) / (1000 * 60 * 60 * 24);
      if (daysDiff < 30) {
        errors.dates = '时间跨度至少30天';
      }
      if (daysDiff > 120) {
        errors.dates = '时间跨度不超过120天';
      }
    }

    setValidationErrors(errors);
    setIsValid(Object.keys(errors).length === 0);
    return Object.keys(errors).length === 0;
  };

  // 网格参数变更处理
  const handleGridParameterChange = (field, value) => {
    // 对于日期字段，直接使用字符串值，不进行数值转换
    const processedValue = (field === 'startDate' || field === 'endDate') ? value : (parseFloat(value) || value);
    const newParams = {
      ...editedGridParams,
      [field]: processedValue
    };
    setEditedGridParams(newParams);
    validateGridParameters(newParams);
  };

  // 手续费参数变更处理
  const handleCommissionChange = (field, value) => {
    setEditedCommissionConfig({
      ...editedCommissionConfig,
      [field]: parseFloat(value),
    });
  };

  // 保存网格参数
  const handleSaveGrid = () => {
    if (validateGridParameters(editedGridParams)) {
      onParametersChange(editedGridParams);
      setIsEditingGrid(false);
      onRunBacktest();
    }
  };

  // 保存手续费参数
  const handleSaveCommission = () => {
    onConfigChange(editedCommissionConfig);
    setIsEditingCommission(false);
    onRunBacktest();
  };

  // 重置网格参数
  const handleResetGrid = () => {
    if (gridStrategy && inputParameters) {
      const defaultParams = {
        priceLower: gridStrategy.price_range?.lower || 0,
        priceUpper: gridStrategy.price_range?.upper || 0,
        totalCapital: inputParameters.total_capital || inputParameters.totalCapital || 0,
        benchmarkPrice: gridStrategy.current_price || 0,
        gridStepSize: gridStrategy.grid_config?.type?.includes('等比')
          ? (gridStrategy.grid_config?.step_ratio || 0) * 100
          : (gridStrategy.grid_config?.step_size || 0),
        singleTradeQuantity: gridStrategy.grid_config?.single_trade_quantity || 0,
        startDate: defaultDates?.startDate || '',
        endDate: defaultDates?.endDate || ''
      };
      setEditedGridParams(defaultParams);
      setValidationErrors({});
      setIsValid(true);
    }
  };

  // 重置手续费参数
  const handleResetCommission = () => {
    const defaultConfig = {
      commissionRate: 0.0002,
      minCommission: 5.0,
      riskFreeRate: 0.03,
      tradingDaysPerYear: 244,
    };
    setEditedCommissionConfig(defaultConfig);
    onConfigChange(defaultConfig);
  };

  // 如果不可见，返回简洁的触发按钮
  if (!isVisible) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <button
          onClick={() => {}}
          className="w-full btn btn-secondary flex items-center justify-center gap-2"
        >
          <Settings className="w-4 h-4" />
          展示网格参数设置
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 sm:p-6">
      {/* 标题区域 */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <Settings className="w-5 h-5 text-green-600" />
          </div>
          <div className="flex-1">
            <h4 className="font-semibold text-gray-900">网格参数设置</h4>
            <p className="text-sm text-gray-600">调整网格策略参数进行个性化回测</p>
          </div>
        </div>
        {/* 编辑手续费按钮 - 在网格参数显示模式时显示 */}
        {!isEditingCommission && (
          <button
            onClick={() => setIsEditingCommission(true)}
            className="btn btn-secondary w-full sm:w-auto sm:ml-auto"
          >
            <Calculator className="w-4 h-4 mr-2" />
            编辑手续费
          </button>
        )}
        {/* 验证状态指示器 - 在网格参数显示模式时显示 */}
        {!isEditingCommission && (
          <div className="flex items-center gap-2">
            {isValid ? (
              <CheckCircle className="w-4 h-4 text-green-600" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-orange-600" />
            )}
            <span className={`text-sm ${isValid ? 'text-green-600' : 'text-orange-600'}`}>
              {isValid ? '参数有效' : '参数需调整'}
            </span>
          </div>
        )}
      </div>

      {/* 网格参数显示模式 */}
      {!isEditingGrid && !isEditingCommission && (
        <div className="space-y-4">
          {/* 参数概览卡片 */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
            <div className="text-center p-3 sm:p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center justify-center w-8 h-8 mx-auto mb-2 bg-blue-100 rounded-full">
                <TrendingUp className="w-4 h-4 text-blue-600" />
              </div>
              <p className="text-sm text-gray-600 mb-1">价格区间</p>
              <p className="text-lg font-bold text-gray-900">
                ¥{editedGridParams.priceLower?.toFixed(3)} - ¥{editedGridParams.priceUpper?.toFixed(3)}
              </p>
            </div>

            <div className="text-center p-3 sm:p-4 bg-green-50 rounded-lg">
              <div className="flex items-center justify-center w-8 h-8 mx-auto mb-2 bg-green-100 rounded-full">
                <DollarSign className="w-4 h-4 text-green-600" />
              </div>
              <p className="text-sm text-gray-600 mb-1">投资金额</p>
              <p className="text-lg font-bold text-gray-900">
                ¥{(editedGridParams.totalCapital || 0).toLocaleString()}
              </p>
            </div>

            <div className="text-center p-3 sm:p-4 bg-purple-50 rounded-lg">
              <div className="flex items-center justify-center w-8 h-8 mx-auto mb-2 bg-purple-100 rounded-full">
                <Target className="w-4 h-4 text-purple-600" />
              </div>
              <p className="text-sm text-gray-600 mb-1">基准价格</p>
              <p className="text-lg font-bold text-gray-900">
                ¥{editedGridParams.benchmarkPrice?.toFixed(3)}
              </p>
            </div>

            <div className="text-center p-3 sm:p-4 bg-orange-50 rounded-lg">
              <div className="flex items-center justify-center w-8 h-8 mx-auto mb-2 bg-orange-100 rounded-full">
                <Hash className="w-4 h-4 text-orange-600" />
              </div>
              <p className="text-sm text-gray-600 mb-1">网格步长</p>
              <p className="text-lg font-bold text-gray-900">
                {gridStrategy?.grid_config?.type?.includes('等比') ? `${editedGridParams.gridStepSize?.toFixed(2)}% (等比)` : `¥${editedGridParams.gridStepSize?.toFixed(3)}`}
              </p>
            </div>

            <div className="text-center p-3 sm:p-4 bg-red-50 rounded-lg">
              <div className="flex items-center justify-center w-8 h-8 mx-auto mb-2 bg-red-100 rounded-full">
                <Calculator className="w-4 h-4 text-red-600" />
              </div>
              <p className="text-sm text-gray-600 mb-1">单笔数量</p>
              <p className="text-lg font-bold text-gray-900">
                {editedGridParams.singleTradeQuantity}股
              </p>
            </div>

            <div className="text-center p-3 sm:p-4 bg-yellow-50 rounded-lg">
              <div className="flex items-center justify-center w-8 h-8 mx-auto mb-2 bg-yellow-100 rounded-full">
                <Calendar className="w-4 h-4 text-yellow-600" />
              </div>
              <p className="text-sm text-gray-600 mb-1">回测区间</p>
              <p className="text-lg font-bold text-gray-900">
                {editedGridParams.startDate && editedGridParams.endDate
                  ? `${editedGridParams.startDate} 至 ${editedGridParams.endDate}`
                  : '未设置'
                }
              </p>
            </div>

          </div>

          {/* 错误提示 */}
          {Object.keys(validationErrors).length > 0 && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-red-600 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-800">参数验证错误</p>
                  <ul className="text-sm text-red-700 mt-1">
                    {Object.values(validationErrors).map((error, index) => (
                      <li key={index}>• {error}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* 操作按钮 */}
          <div className="flex gap-3 pt-4">
            <button
              onClick={() => setIsEditingGrid(true)}
              className="btn btn-primary flex-1"
            >
              编辑参数
            </button>
          </div>
        </div>
      )}

      {/* 网格参数编辑模式 */}
      {isEditingGrid && !isEditingCommission && (
        <div className="space-y-4 sm:space-y-6">
          {/* 回测区间参数 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-yellow-600" />
                  开始日期
                </div>
                <span className="text-xs text-gray-500 font-normal">回测开始日期</span>
              </label>
              <input
                type="date"
                value={editedGridParams.startDate || ''}
                onChange={(e) => handleGridParameterChange('startDate', e.target.value)}
                className="input"
              />
            </div>

            <div>
              <label className="label">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-yellow-600" />
                  结束日期
                </div>
                <span className="text-xs text-gray-500 font-normal">回测结束日期</span>
              </label>
              <input
                type="date"
                value={editedGridParams.endDate || ''}
                onChange={(e) => handleGridParameterChange('endDate', e.target.value)}
                className="input"
              />
            </div>
          </div>

          {validationErrors.dates && (
            <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
              {validationErrors.dates}
            </div>
          )}

          {/* 价格区间参数 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-blue-600" />
                  价格下限 (元)
                </div>
                <span className="text-xs text-gray-500 font-normal">买入区间下限</span>
              </label>
              <input
                type="number"
                step="0.001"
                value={editedGridParams.priceLower || ''}
                onChange={(e) => handleGridParameterChange('priceLower', e.target.value)}
                className="input"
                placeholder="输入价格下限"
              />
            </div>

            <div>
              <label className="label">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-blue-600" />
                  价格上限 (元)
                </div>
                <span className="text-xs text-gray-500 font-normal">卖出区间上限</span>
              </label>
              <input
                type="number"
                step="0.001"
                value={editedGridParams.priceUpper || ''}
                onChange={(e) => handleGridParameterChange('priceUpper', e.target.value)}
                className="input"
                placeholder="输入价格上限"
              />
            </div>
          </div>

          {validationErrors.priceRange && (
            <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
              {validationErrors.priceRange}
            </div>
          )}

          {/* 基准价格和投资金额 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-purple-600" />
                  基准价格 (元)
                </div>
                <span className="text-xs text-gray-500 font-normal">网格中心价格，通常为当前价格</span>
              </label>
              <input
                type="number"
                step="0.001"
                value={editedGridParams.benchmarkPrice || ''}
                onChange={(e) => handleGridParameterChange('benchmarkPrice', e.target.value)}
                className="input"
                placeholder="输入基准价格"
              />
            </div>

            <div>
              <label className="label">
                <div className="flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-green-600" />
                  投资金额 (元)
                </div>
                <span className="text-xs text-gray-500 font-normal">总投资资金量，1000-1000万</span>
              </label>
              <input
                type="number"
                step="1000"
                min="1000"
                max="10000000"
                value={editedGridParams.totalCapital || ''}
                onChange={(e) => handleGridParameterChange('totalCapital', e.target.value)}
                className="input"
                placeholder="输入投资金额"
              />
            </div>
          </div>

          {validationErrors.benchmarkPrice && (
            <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
              {validationErrors.benchmarkPrice}
            </div>
          )}

          {validationErrors.totalCapital && (
            <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
              {validationErrors.totalCapital}
            </div>
          )}

          {/* 网格步长和单笔数量 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">
                <div className="flex items-center gap-2">
                  <Hash className="w-4 h-4 text-orange-600" />
                  网格步长 ({gridStrategy?.grid_config?.type?.includes('等比') ? '比例' : '元'})
                </div>
                <span className="text-xs text-gray-500 font-normal">{gridStrategy?.grid_config?.type?.includes('等比') ? '相邻网格间的比例差' : '相邻网格间的价格差'}</span>
              </label>
              <input
                type="number"
                step="0.001"
                min="0.001"
                value={editedGridParams.gridStepSize || ''}
                onChange={(e) => handleGridParameterChange('gridStepSize', e.target.value)}
                className="input"
                placeholder="输入网格步长"
              />
            </div>

            <div>
              <label className="label">
                <div className="flex items-center gap-2">
                  <Calculator className="w-4 h-4 text-red-600" />
                  单笔数量 (股)
                </div>
                <span className="text-xs text-gray-500 font-normal">每次交易的股票数量</span>
              </label>
              <input
                type="number"
                step="1"
                min="1"
                value={editedGridParams.singleTradeQuantity || ''}
                onChange={(e) => handleGridParameterChange('singleTradeQuantity', e.target.value)}
                className="input"
                placeholder="输入单笔数量"
              />
            </div>
          </div>


          {/* 操作按钮 */}
          <div className="space-y-3 pt-4">
            <button
              onClick={handleSaveGrid}
              disabled={!isValid}
              className="btn btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
            >
              保存并重新回测
            </button>

            <div className="flex gap-3">
              <button
                onClick={handleResetGrid}
                className="btn btn-secondary flex-1"
              >
                重置
              </button>
              <button
                onClick={() => setIsEditingGrid(false)}
                className="btn btn-secondary flex-1"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 手续费编辑模式 */}
      {isEditingCommission && (
        <div className="space-y-4 sm:space-y-6">
          {/* 手续费参数 - 双栏结构 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                value={(editedCommissionConfig.commissionRate * 100).toFixed(3)}
                onChange={(e) => handleCommissionChange('commissionRate', parseFloat(e.target.value) / 100)}
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
                value={editedCommissionConfig.minCommission}
                onChange={(e) => handleCommissionChange('minCommission', e.target.value)}
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
                value={(editedCommissionConfig.riskFreeRate * 100).toFixed(1)}
                onChange={(e) => handleCommissionChange('riskFreeRate', parseFloat(e.target.value) / 100)}
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
                value={editedCommissionConfig.tradingDaysPerYear}
                onChange={(e) => handleCommissionChange('tradingDaysPerYear', e.target.value)}
                className="input"
              />
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="space-y-3 pt-4">
            <button
              onClick={handleSaveCommission}
              className="btn btn-primary w-full"
            >
              保存并重新回测
            </button>

            <div className="flex gap-3">
              <button
                onClick={handleResetCommission}
                className="btn btn-secondary flex-1"
              >
                重置
              </button>
              <button
                onClick={() => setIsEditingCommission(false)}
                className="btn btn-secondary flex-1"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { runBacktest } from '@shared/services/api';
import { hashString, safeSetSessionStorage, safeGetSessionStorage } from '@shared/utils';
import BacktestGuide from './backtest/BacktestGuide';
import GridParameterSettings from './backtest/GridParameterSettings';
import BacktestMetrics from './backtest/BacktestMetrics';
import BacktestCharts from './backtest/BacktestCharts';
import TradeList from './backtest/TradeList';
import GridPerformance from './backtest/GridPerformance';
import BacktestLoading from './backtest/BacktestLoading';
import BacktestError from './backtest/BacktestError';

/**
 * 回测分析标签页
 */
export default function BacktestTab({ etfCode, exchangeCode, gridStrategy, type, totalCapital, autoEditParams = false, onGridApplied, onSuitabilityApplied }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [backtestResult, setBacktestResult] = useState(null);
  const [backtestConfig, setBacktestConfig] = useState({
    commissionRate: 0.0002,
    minCommission: 5,
    riskFreeRate: 0.03,
    tradingDaysPerYear: 244,
  });
  const [customGridParams, setCustomGridParams] = useState(null);

  // 从localStorage加载回测配置
  useEffect(() => {
    const saved = localStorage.getItem('backtestConfig');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setBacktestConfig(parsed);
      } catch (e) {
        console.error('加载缓存的回测配置失败', e);
      }
    }
  }, []);

  // 保存回测配置到localStorage
  useEffect(() => {
    localStorage.setItem('backtestConfig', JSON.stringify(backtestConfig));
  }, [backtestConfig]);

  // 联动：把回测实际使用的网格（后端返回，含自定义/重对齐后的参数）上报给父组件，
  // 使"网格策略"标签与"回测分析"保持一致。
  useEffect(() => {
    if (backtestResult?.grid_strategy && typeof onGridApplied === 'function') {
      onGridApplied(backtestResult.grid_strategy);
    }
  }, [backtestResult, onGridApplied]);

  // 联动：把回测算出的适宜度评估（方案A，基于实测）上报，
  // 使"概览""适宜度评估"标签与"回测分析"完全同源一致。
  useEffect(() => {
    if (backtestResult?.suitability_evaluation && typeof onSuitabilityApplied === 'function') {
      onSuitabilityApplied(backtestResult.suitability_evaluation);
    }
  }, [backtestResult, onSuitabilityApplied]);

  // 自定义网格参数变更处理
  const handleCustomGridParamsChange = useCallback((newParams) => {
    setCustomGridParams(newParams);
    // 当自定义参数改变时，清除当前结果以准备重新回测
    setBacktestResult(null);
  }, []);

  // 缓存回测结果的key (包含自定义参数)
  const cacheKey = useMemo(() => {
    const keyData = { etfCode, exchangeCode, type, gridStrategy, backtestConfig, customGridParams };
    return `backtest_${hashString(JSON.stringify(keyData))}`;
  }, [etfCode, exchangeCode, type, gridStrategy, backtestConfig, customGridParams]);

  const handleRunBacktest = useCallback(async () => {
    console.log('handleRunBacktest called');
    console.log('customGridParams:', customGridParams);
    setLoading(true);
    setError(null);

    try {
      console.log('Calling runBacktest API...');
      const response = await runBacktest(etfCode, exchangeCode, gridStrategy, backtestConfig, type, customGridParams);
      console.log('API response received:', response);
      const result = response.data; // 提取实际数据
      console.log('Extracted result:', result);
      // 缓存结果
      const success = safeSetSessionStorage(cacheKey, JSON.stringify(result));
      if (!success) {
        console.warn('Failed to cache backtest result due to storage quota');
      }
      setBacktestResult(result);
      console.log('Backtest result set successfully');
    } catch (err) {
      console.error('Backtest error:', err);
      setError(err.message || '回测执行失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, [etfCode, exchangeCode, gridStrategy, backtestConfig, type, customGridParams, cacheKey]);

  useEffect(() => {
    console.log('BacktestTab useEffect triggered:', { etfCode, exchangeCode, gridStrategy: !!gridStrategy, type });
    if (etfCode && exchangeCode && gridStrategy) {
      console.log('Starting backtest for:', etfCode);
      // 尝试从缓存读取
      const cachedData = safeGetSessionStorage(cacheKey);
      if (cachedData) {
        setBacktestResult(cachedData);
        console.log('Loaded from cache');
        return;
      }

      // 执行回测
      console.log('Executing backtest...');
      handleRunBacktest();
    } else {
      console.log('Backtest not triggered: missing etfCode, exchangeCode or gridStrategy');
    }
  }, [etfCode, exchangeCode, type, gridStrategy, cacheKey, handleRunBacktest]);

  return (
    <div className="space-y-6">
      

      {/* 网格参数设置 */}
      <GridParameterSettings
        gridStrategy={backtestResult?.grid_strategy || gridStrategy}
        inputParameters={{ totalCapital, total_capital: totalCapital }}
        defaultDates={backtestResult?.backtest_period}
        backtestConfig={backtestConfig}
        onConfigChange={setBacktestConfig}
        onParametersChange={handleCustomGridParamsChange}
        onRunBacktest={handleRunBacktest}
        isVisible={true}
        autoEditParams={autoEditParams}
      />

      {loading && <BacktestLoading />}

      {error && <BacktestError error={error} onRetry={handleRunBacktest} />}

      {!loading && !error && !backtestResult && (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">暂无回测数据</p>
          <button
            onClick={handleRunBacktest}
            className="btn btn-primary"
          >
            开始回测
          </button>
        </div>
      )}

      {backtestResult && (
        <>
          {/* 指标概览 */}
          <BacktestMetrics
            metrics={backtestResult.performance_metrics}
            tradingMetrics={backtestResult.trading_metrics}
            benchmark={backtestResult.benchmark_comparison}
            period={backtestResult.backtest_period}
          />

          {/* 图表展示 */}
          <BacktestCharts
            priceCurve={backtestResult.price_curve}
            equityCurve={backtestResult.equity_curve}
            tradeRecords={backtestResult.trade_records}
            gridStrategy={backtestResult?.grid_strategy || gridStrategy}
          />

          {/* 交易记录 */}
          <TradeList
            trades={backtestResult.trade_records}
            gridStrategy={backtestResult?.grid_strategy || gridStrategy}
            totalCapital={totalCapital}
          />

          {/* 网格表现分析 
          <GridPerformance
            gridAnalysis={backtestResult.grid_analysis}
            priceLevels={gridStrategy.price_levels}
          />
          */}
        </>
      )}

      {/* 功能引导 */}
      <BacktestGuide period={backtestResult?.backtest_period} />
    </div>
  );
}
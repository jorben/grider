import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { runBacktest } from '@shared/services/api';
import { hashString } from '@shared/utils';
import BacktestGuide from './backtest/BacktestGuide';
import BacktestConfigEditor from './backtest/BacktestConfigEditor';
import BacktestMetrics from './backtest/BacktestMetrics';
import BacktestCharts from './backtest/BacktestCharts';
import TradeList from './backtest/TradeList';
import GridPerformance from './backtest/GridPerformance';
import BacktestLoading from './backtest/BacktestLoading';
import BacktestError from './backtest/BacktestError';

/**
 * 回测分析标签页
 */
export default function BacktestTab({ etfCode, exchangeCode, gridStrategy, type, totalCapital }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [backtestResult, setBacktestResult] = useState(null);
  const [backtestConfig, setBacktestConfig] = useState({
    commissionRate: 0.0002,
    minCommission: 5,
    riskFreeRate: 0.03,
    tradingDaysPerYear: 244,
  });

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

  // 缓存回测结果的key
  const cacheKey = useMemo(() => {
    const keyData = { etfCode, exchangeCode, type, gridStrategy, backtestConfig };
    return `backtest_${hashString(JSON.stringify(keyData))}`;
  }, [etfCode, exchangeCode, type, gridStrategy, backtestConfig]);

  const handleRunBacktest = useCallback(async () => {
    console.log('handleRunBacktest called');
    setLoading(true);
    setError(null);

    try {
      console.log('Calling runBacktest API...');
      const response = await runBacktest(etfCode, exchangeCode, gridStrategy, backtestConfig, type);
      console.log('API response received:', response);
      const result = response.data; // 提取实际数据
      console.log('Extracted result:', result);
      // 缓存结果
      sessionStorage.setItem(cacheKey, JSON.stringify(result));
      setBacktestResult(result);
      console.log('Backtest result set successfully');
    } catch (err) {
      console.error('Backtest error:', err);
      setError(err.message || '回测执行失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, [etfCode, exchangeCode, gridStrategy, backtestConfig, type, cacheKey]);

  useEffect(() => {
    console.log('BacktestTab useEffect triggered:', { etfCode, exchangeCode, gridStrategy: !!gridStrategy, type });
    if (etfCode && exchangeCode && gridStrategy) {
      console.log('Starting backtest for:', etfCode);
      // 尝试从缓存读取
      const cached = sessionStorage.getItem(cacheKey);
      if (cached) {
        try {
          const cachedData = JSON.parse(cached);
          setBacktestResult(cachedData);
          console.log('Loaded from cache');
          return;
        } catch (e) {
          console.error('缓存解析失败', e);
        }
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
      

      {/* 参数编辑器 */}
      <BacktestConfigEditor
        config={backtestConfig}
        onConfigChange={setBacktestConfig}
        onRunBacktest={handleRunBacktest}
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
            gridStrategy={gridStrategy}
          />

          {/* 交易记录 */}
          <TradeList
            trades={backtestResult.trade_records}
            gridStrategy={gridStrategy}
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
      <BacktestGuide />
    </div>
  );
}
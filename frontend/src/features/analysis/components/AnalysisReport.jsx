import React, { useState, useEffect, lazy, Suspense } from "react";
import { LoadingSpinner } from "@shared/components/ui";
import ReportTabs from "./ReportTabs";
import OverviewTab from "./OverviewTab";
import ErrorState from "./ErrorState";
import SuitabilityCard from "./ReportCards/SuitabilityCard";
import GridParametersCard from "./ReportCards/GridParametersCard";

// 懒加载回测组件
const BacktestTab = lazy(() => import("./BacktestTab"));

/**
 * 分析报告容器组件
 * 负责协调各个报告子组件和状态管理
 */
const AnalysisReport = ({
  data,
  loading,
  onBackToInput,
  onReAnalysis,
  editParamsFirst = false,
  onEffectiveCapitalChange,
}) => {
  const [activeTab, setActiveTab] = useState(editParamsFirst ? "backtest" : "overview");
  // 从首页勾选"分析前自定义参数"进入时，自动切到回测标签（仅一次，之后尊重用户手动切换）
  const [autoTabApplied, setAutoTabApplied] = useState(false);
  useEffect(() => {
    if (editParamsFirst && !autoTabApplied) {
      setActiveTab("backtest");
      setAutoTabApplied(true);
    }
  }, [editParamsFirst, autoTabApplied]);

  // 回测标签一旦被访问就保持挂载（用 CSS 隐藏而非卸载），
  // 这样切换标签后用户编辑的参数与回测结果不会丢失。
  const [backtestMounted, setBacktestMounted] = useState(editParamsFirst);
  useEffect(() => {
    if (activeTab === "backtest") setBacktestMounted(true);
  }, [activeTab]);

  // 联动：回测分析里实际使用的网格（含用户自定义参数）。
  // 用户在回测中改了参数后，"网格策略"标签也显示同一套网格。
  const [effectiveGrid, setEffectiveGrid] = useState(null);
  // 联动：回测算出的适宜度评估（方案A）。一旦回测产出，三个标签统一使用这份。
  const [effectiveSuitability, setEffectiveSuitability] = useState(null);

  // 把回测自定义后实际使用的投资金额上报给父组件（顶部标题用），保持口径一致
  useEffect(() => {
    if (!onEffectiveCapitalChange) return;
    if (effectiveGrid) {
      let cap = effectiveGrid.total_capital;
      if (!cap && effectiveGrid.fund_allocation) {
        const fa = effectiveGrid.fund_allocation;
        cap = (fa.base_position_amount || 0) + (fa.grid_trading_amount || 0) + (fa.reserve_amount || 0);
      }
      if (cap > 0) onEffectiveCapitalChange(Math.round(cap));
    }
  }, [effectiveGrid, onEffectiveCapitalChange]);


  // 显示加载状态
  if (loading) {
    return (
      <LoadingSpinner
        message="正在分析标的数据..."
        showProgress={true}
        progress={75}
      />
    );
  }

  // 显示错误状态
  if (data?.error) {
    return (
      <ErrorState
        type="error"
        message={data.message}
        onBackToInput={onBackToInput}
        onReAnalysis={onReAnalysis}
      />
    );
  }

  if (!data) return null;

  const {
    etf_info,
    data_quality,
    suitability_evaluation,
    grid_strategy,
    strategy_rationale,
    adjustment_suggestions,
    input_parameters,
  } = data;

  // 数据完整性检查
  const isDataComplete = () => {
    if (!suitability_evaluation || !grid_strategy || !etf_info) {
      return false;
    }

    const dataObjects = {
      suitability_evaluation: suitability_evaluation,
      grid_strategy: grid_strategy,
      etf_info: etf_info,
    };

    const requiredFields = {
      suitability_evaluation: ["total_score", "conclusion"],
      grid_strategy: ["grid_config", "fund_allocation"],
      etf_info: ["code", "name", "current_price"],
    };

    for (const [objName, fields] of Object.entries(requiredFields)) {
      const obj = dataObjects[objName];
      for (const field of fields) {
        if (obj[field] === undefined || obj[field] === null) {
          return false;
        }
      }
    }

    return true;
  };

  if (!isDataComplete()) {
    return (
      <ErrorState
        type="data_incomplete"
        message="分析数据不完整，请重新分析"
        onBackToInput={onBackToInput}
        onReAnalysis={onReAnalysis}
      />
    );
  }

  // 统一"投资资金"口径：一旦在回测中自定义并应用了网格(effectiveGrid)，
  // 投资资金以该网格 fund_allocation(底仓+网格+预留)之和为准——它精确等于回测实际使用的总资金，
  // 从而保证 概览/网格策略/回测分析 三个标签的投资金额完全一致（修复显示100万但实际95000的矛盾）。
  const effectiveInputParameters = (() => {
    if (effectiveGrid) {
      // 优先用后端显式返回的实际总资金；否则回退到 fund_allocation 三部分之和
      let cap = effectiveGrid.total_capital;
      if (!cap && effectiveGrid.fund_allocation) {
        const fa = effectiveGrid.fund_allocation;
        cap = (fa.base_position_amount || 0) + (fa.grid_trading_amount || 0) + (fa.reserve_amount || 0);
      }
      if (cap > 0) {
        return { ...input_parameters, total_capital: Math.round(cap) };
      }
    }
    return input_parameters;
  })();

  return (
    <div className="space-y-6">
      {/* 标签页导航 */}
      <div className="bg-white rounded-xl shadow-lg">
        <ReportTabs activeTab={activeTab} onTabChange={setActiveTab} />

        <div className="p-6">
          {/* 概览标签页 */}
          {activeTab === "overview" && (
            <OverviewTab
              etfInfo={etf_info}
              suitabilityEvaluation={effectiveSuitability || suitability_evaluation}
              gridStrategy={effectiveGrid || grid_strategy}
              dataQuality={data_quality}
              inputParameters={effectiveInputParameters}
            />
          )}

          {/* 适宜度评估标签页 */}
          {activeTab === "suitability" && (
            <SuitabilityCard
              evaluation={effectiveSuitability || suitability_evaluation}
              dataQuality={data_quality}
              showDetailed={true}
              isCustomized={!!effectiveSuitability}
            />
          )}

          {/* 网格策略标签页 */}
          {activeTab === "strategy" && (
            <GridParametersCard
              gridStrategy={effectiveGrid || grid_strategy}
              inputParameters={effectiveInputParameters}
              strategyRationale={strategy_rationale}
              adjustmentSuggestions={adjustment_suggestions}
              showDetailed={true}
              dataQuality={data_quality}
              etfInfo={etf_info}
              isCustomized={!!effectiveGrid}
            />
          )}

          {/* 回测分析标签页：一旦挂载就保留（用 display 隐藏），避免切换标签丢失编辑参数 */}
          {backtestMounted && (
            <div style={{ display: activeTab === "backtest" ? "block" : "none" }}>
              <Suspense fallback={<div className="text-center py-12">加载中...</div>}>
                <BacktestTab
                  etfCode={etf_info.code}
                  exchangeCode={etf_info.exchange_code}
                  gridStrategy={grid_strategy}
                  type={etf_info.type}
                  totalCapital={input_parameters.total_capital}
                  autoEditParams={editParamsFirst}
                  onGridApplied={setEffectiveGrid}
                  onSuitabilityApplied={setEffectiveSuitability}
                />
              </Suspense>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnalysisReport;

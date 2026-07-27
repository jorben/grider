import React, { useState, useCallback } from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { ArrowLeft, GitCompare, Info, Plus, X } from "lucide-react";
import { analyzeETF, runBacktest } from "@shared/services/api";
import CustomCodeList from "@features/etf/components/CustomCodeList";
import CompareMetricsTable from "@features/compare/CompareMetricsTable";
import CompareReturnChart from "@features/compare/CompareReturnChart";
import CompareTradeChart from "@features/compare/CompareTradeChart";

const COLORS = ["#2563eb", "#f59e0b", "#10b981", "#ec4899", "#0ea5e9"];
const toYMD = (d) => d.toISOString().slice(0, 10);
const DEFAULT_END = toYMD(new Date());
const DEFAULT_START = "2020-01-01";
const MAX_SLOTS = 5;

/** equity_curve + price_curve -> 累计收益率点序列 [{time, strat, hold}] */
function toReturnPoints(result, initCapital) {
  const eq = result?.equity_curve || [];
  const price = result?.price_curve || [];
  if (!eq.length || !price.length) return [];
  const initAsset = eq[0]?.total_asset || initCapital;
  const firstClose = price[0]?.close;
  const closeMap = new Map(price.map((p) => [p.time, p.close]));
  return eq.map((pt) => {
    const close = closeMap.get(pt.time);
    return {
      time: (pt.time || "").slice(0, 10),
      strat: initAsset ? pt.total_asset / initAsset - 1 : null,
      hold: firstClose && close != null ? close / firstClose - 1 : null,
    };
  });
}

export default function GridComparePage() {
  const [capital, setCapital] = useState(100000);
  const [gridType, setGridType] = useState("等比");
  const [riskPreference, setRiskPreference] = useState("均衡");
  const [startDate, setStartDate] = useState(DEFAULT_START);
  const [endDate, setEndDate] = useState(DEFAULT_END);
  // 全局网格步长（留空=各标的按 ATR 自动；填值=全局统一应用，等比按%、等差按元）
  const [gridStep, setGridStep] = useState("");

  const [codes, setCodes] = useState(["510300", "159915"]);
  const [activeSlot, setActiveSlot] = useState(0);

  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState("");
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);

  const setCodeAt = (idx, val) => {
    setCodes((prev) => {
      const next = [...prev];
      next[idx] = (val || "").replace(/[^0-9a-zA-Z]/g, "").toUpperCase();
      return next;
    });
  };

  const addSlot = () => {
    setCodes((prev) => (prev.length >= MAX_SLOTS ? prev : [...prev, ""]));
  };

  const removeSlot = (idx) => {
    setCodes((prev) => (prev.length <= 2 ? prev : prev.filter((_, i) => i !== idx)));
    setActiveSlot((s) => (s >= idx && s > 0 ? s - 1 : s));
  };

  const handleRun = useCallback(async () => {
    setError(null);
    const valid = codes.map((c) => c.trim()).filter(Boolean);
    if (valid.length < 2) {
      setError("请至少填写 2 个标的代码进行对比");
      return;
    }
    setLoading(true);
    setResults(null);
    try {
      const out = [];
      for (let i = 0; i < codes.length; i++) {
        const code = codes[i].trim();
        if (!code) {
          out.push(null);
          continue;
        }
        setProgress(`正在分析并回测 ${code}（${i + 1}/${valid.length}）...`);
        // 1) 分析：按 ATR 为该标的生成网格 + 取得 etf_info
        const analysis = await analyzeETF({
          etfCode: code,
          totalCapital: Number(capital),
          gridType,
          riskPreference,
          adjustmentCoefficient: 1.0,
        });
        if (!analysis.success) throw new Error(analysis.message || `${code} 分析失败`);
        const info = analysis.data.etf_info;
        const gridStrategy = analysis.data.grid_strategy;

        // 2) 回测：同区间，复用该标的的 ATR 网格；如填了全局步长则统一应用
        const customParams = { startDate: startDate || undefined, endDate: endDate || undefined };
        const stepVal = parseFloat(gridStep);
        if (gridStep !== "" && !isNaN(stepVal) && stepVal > 0) {
          customParams.gridStepSize = stepVal; // 等比按%，等差按元
        }
        const bt = await runBacktest(
          info.code,
          info.exchange_code,
          gridStrategy,
          null,
          info.type,
          customParams
        );
        const d = bt.data;
        const m = d.performance_metrics || {};
        const bm = d.benchmark_comparison || {};
        const tm = d.trading_metrics || {};
        out.push({
          code: info.code,
          name: info.name || code,
          color: COLORS[i] || "#10b981",
          metrics: {
            total_return: m.total_return,
            excess_return: bm.excess_return,
            annualized_return: m.annualized_return,
            hold_return: bm.hold_return,
            max_drawdown: m.max_drawdown,
            sharpe_ratio: m.sharpe_ratio,
            win_rate: tm.win_rate,
            trades: tm.total_trades,
          },
          points: toReturnPoints(d, Number(capital)),
          raw: d,
        });
      }
      setResults(out);
    } catch (e) {
      setError(e.message || "对比回测失败，请稍后重试");
    } finally {
      setLoading(false);
      setProgress("");
    }
  }, [codes, capital, gridType, riskPreference, startDate, endDate, gridStep]);

  const validResults = (results || []).filter(Boolean);

  return (
    <>
      <Helmet>
        <title>网格策略对比回测</title>
      </Helmet>

      <div className="space-y-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <GitCompare className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">网格策略对比回测</h1>
                <p className="text-sm text-gray-600">
                  同一资金/类型/区间下，对比最多 5 个标的的网格策略表现
                </p>
              </div>
            </div>
            <Link to="/" className="flex items-center gap-1 text-sm text-gray-600 hover:text-blue-600">
              <ArrowLeft className="w-4 h-4" />
              返回首页
            </Link>
          </div>
          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start gap-2">
            <Info className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-blue-800">
              网格的价格区间由每个标的的 ATR 自动生成（因不同标的价位差异大，强制共用区间无意义）；
              共用的是资金、网格类型、频率偏好、回测区间与（可选）全局网格步长。
              2 个标的时收益曲线默认双 Y 轴（左A右B）；3 个及以上自动单轴归一化，默认仅显示策略线（可开关持有线）。
            </p>
          </div>
        </div>

        {/* 公共参数 */}
        <div className="bg-white rounded-xl shadow-lg p-6 space-y-5">
          <h2 className="font-semibold text-gray-900">公共参数（所有标的共用）</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">投资金额（元）</label>
              <input
                type="number"
                value={capital}
                onChange={(e) => setCapital(e.target.value)}
                step="10000"
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">开始日期</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">结束日期</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-2">网格类型</label>
              <div className="flex gap-2">
                {["等比", "等差"].map((t) => (
                  <button
                    key={t}
                    onClick={() => setGridType(t)}
                    className={`px-4 py-2 rounded-lg text-sm border transition-colors ${
                      gridType === t
                        ? "bg-blue-600 text-white border-blue-600"
                        : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                    }`}
                  >
                    {t}网格
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-2">频率偏好</label>
              <div className="flex gap-2">
                {["低频", "均衡", "高频"].map((t) => (
                  <button
                    key={t}
                    onClick={() => setRiskPreference(t)}
                    className={`px-4 py-2 rounded-lg text-sm border transition-colors ${
                      riskPreference === t
                        ? "bg-blue-600 text-white border-blue-600"
                        : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-2">
                全局网格步长（{gridType === "等比" ? "%" : "元"}，可选）
              </label>
              <input
                type="number"
                value={gridStep}
                onChange={(e) => setGridStep(e.target.value)}
                step={gridType === "等比" ? "0.5" : "0.01"}
                min="0"
                placeholder={`留空=各标的按ATR自动`}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
              <p className="text-xs text-gray-500 mt-1">
                填值则所有标的统一用该步长（{gridType === "等比" ? "如 5 表示 5%" : "相邻网格价差"}），
                留空则各标的按自身 ATR 自动。
              </p>
            </div>
          </div>
        </div>

        {/* 对比标的 */}
        <div className="bg-white rounded-xl shadow-lg p-6 space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h2 className="font-semibold text-gray-900">对比标的（{codes.length} 个，最多 {MAX_SLOTS}）</h2>
            <button
              onClick={addSlot}
              disabled={codes.length >= MAX_SLOTS}
              className="flex items-center gap-1 text-sm px-3 py-1.5 rounded-lg border border-blue-300 text-blue-600 hover:bg-blue-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Plus className="w-4 h-4" />
              添加标的
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {codes.slice(0, MAX_SLOTS).map((c, i) => (
              <div
                key={i}
                className={`border rounded-lg p-3 ${
                  activeSlot === i ? "border-blue-400 ring-1 ring-blue-200" : "border-gray-200"
                }`}
                onClick={() => setActiveSlot(i)}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="inline-block w-3 h-3 rounded-full" style={{ background: COLORS[i] }} />
                  <span className="text-sm font-medium text-gray-700">
                    标的 {String.fromCharCode(65 + i)}
                  </span>
                  {codes.length > 2 && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        removeSlot(i);
                      }}
                      className="ml-auto text-gray-400 hover:text-red-500"
                      title="移除该标的"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>
                <input
                  value={c}
                  onChange={(e) => setCodeAt(i, e.target.value)}
                  onFocus={() => setActiveSlot(i)}
                  placeholder="如：510300；场外基金加F，如 F007339"
                  maxLength={7}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                />
              </div>
            ))}
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-2">
              点击下方标的填入「标的 {String.fromCharCode(65 + activeSlot)}」（先点上方卡片切换目标槽位）
            </p>
            <CustomCodeList value={codes[activeSlot]} onSelect={(v) => setCodeAt(activeSlot, v)} />
          </div>

          <button
            onClick={handleRun}
            disabled={loading}
            className="px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
          >
            {loading ? "对比回测中..." : "开始对比回测"}
          </button>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{error}</div>
          )}
        </div>

        {loading && (
          <div className="bg-white rounded-xl shadow-lg p-12 text-center text-gray-600">
            {progress || "正在回测..."}
          </div>
        )}

        {validResults.length > 0 && !loading && (
          <>
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="font-semibold text-gray-900 mb-4">指标对比</h2>
              <CompareMetricsTable items={validResults} />
            </div>
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="font-semibold text-gray-900 mb-4">累计收益曲线对比</h2>
              <CompareReturnChart series={validResults} />
            </div>

            {/* 各标的价格 + 网格上下限 + 买卖点位走势图 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {validResults.map((it) => (
                <div key={it.code} className="bg-white rounded-xl shadow-lg p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="inline-block w-3 h-3 rounded-full" style={{ background: it.color }} />
                    <h2 className="font-semibold text-gray-900">
                      {it.name}（{it.code}） · 价格/网格区间/买卖点
                    </h2>
                  </div>
                  <CompareTradeChart
                    priceCurve={it.raw?.price_curve}
                    tradeRecords={it.raw?.trade_records}
                    gridRange={it.raw?.grid_strategy?.price_range}
                    color={it.color}
                  />
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </>
  );
}

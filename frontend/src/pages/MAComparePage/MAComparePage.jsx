import React, { useState, useCallback } from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { ArrowLeft, GitCompare, Info, Plus, X } from "lucide-react";
import { runMABacktest } from "@shared/services/api";
import CustomCodeList from "@features/etf/components/CustomCodeList";
import CompareMetricsTable from "@features/compare/CompareMetricsTable";
import CompareReturnChart from "@features/compare/CompareReturnChart";
import CompareTradeChart from "@features/compare/CompareTradeChart";

const PRESET_PERIODS = [5, 15, 20, 50, 99, 128, 225];
// 5 标的固定配色：靛蓝 / 琥珀 / 翠绿 / 玫红 / 天蓝
const COLORS = ["#4f46e5", "#f59e0b", "#10b981", "#ec4899", "#0ea5e9"];
const toYMD = (d) => d.toISOString().slice(0, 10);
const DEFAULT_END = toYMD(new Date());
const DEFAULT_START = "2020-01-01";
const MAX_SLOTS = 5; // 最多 5 个标的对比

/** equity_curve + price_curve -> 累计收益率点序列 [{time, strat, hold}] */
function toReturnPoints(result) {
  const eq = result?.equity_curve || [];
  const price = result?.price_curve || [];
  if (!eq.length || !price.length) return [];
  const initAsset = eq[0]?.total_asset;
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

export default function MAComparePage() {
  const [capital, setCapital] = useState(100000);
  const [maType, setMaType] = useState("SMA");
  const [period, setPeriod] = useState(20);
  const [customPeriod, setCustomPeriod] = useState("");
  const [useCustom, setUseCustom] = useState(false);
  const [startDate, setStartDate] = useState(DEFAULT_START);
  const [endDate, setEndDate] = useState(DEFAULT_END);

  // 对比标的槽位（1-5 个，默认 2 个）
  const [codes, setCodes] = useState(["510300", "159915"]);
  const [activeSlot, setActiveSlot] = useState(0); // 自定义列表点选时填入哪个槽

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null); // [{code, name, color, metrics, points} | null]

  const effectivePeriod = useCustom ? parseInt(customPeriod, 10) : period;

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
    setCodes((prev) => {
      if (prev.length <= 2) return prev; // 至少保留 2 个
      const next = prev.filter((_, i) => i !== idx);
      return next;
    });
    setActiveSlot((s) => (s >= idx && s > 0 ? s - 1 : s));
  };

  const handleRun = useCallback(async () => {
    setError(null);
    const valid = codes.map((c) => c.trim()).filter(Boolean);
    if (valid.length < 2) {
      setError("请至少填写 2 个标的代码进行对比");
      return;
    }
    if (!effectivePeriod || effectivePeriod < 2 || effectivePeriod > 500) {
      setError("均线周期应在 2-500 之间");
      return;
    }
    setLoading(true);
    setResults(null);
    try {
      // 串行执行（后端 V8 非线程安全）
      const out = [];
      for (let i = 0; i < codes.length; i++) {
        const code = codes[i].trim();
        if (!code) {
          out.push(null);
          continue;
        }
        const resp = await runMABacktest({
          etfCode: code,
          totalCapital: Number(capital),
          maParams: { period: effectivePeriod, maType },
          startDate: startDate || undefined,
          endDate: endDate || undefined,
        });
        const d = resp.data;
        const m = d.performance_metrics || {};
        const bm = d.benchmark_comparison || {};
        const tm = d.trading_metrics || {};
        out.push({
          code: d.etf_info?.code || code,
          name: d.etf_info?.name || code,
          color: COLORS[i] || "#10b981",
          metrics: {
            total_return: m.total_return,
            excess_return: bm.excess_return,
            annualized_return: m.annualized_return,
            hold_return: bm.hold_return,
            max_drawdown: m.max_drawdown,
            sharpe_ratio: m.sharpe_ratio,
            win_rate: tm.win_rate,
            trades: tm.sell_trades,
          },
          points: toReturnPoints(d),
          raw: d,
        });
      }
      setResults(out);
    } catch (e) {
      setError(e.message || "对比回测失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  }, [codes, capital, maType, effectivePeriod, startDate, endDate]);

  const validResults = (results || []).filter(Boolean);

  return (
    <>
      <Helmet>
        <title>均线策略对比回测</title>
      </Helmet>

      <div className="space-y-6">
        {/* 标题 */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-100 rounded-lg">
                <GitCompare className="w-6 h-6 text-indigo-600" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">均线策略对比回测</h1>
                <p className="text-sm text-gray-600">
                  同一套均线参数下，对比最多 5 个标的的均线策略表现
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Link to="/ma-backtest" className="text-sm text-gray-600 hover:text-indigo-600">
                单标的回测
              </Link>
              <Link to="/" className="flex items-center gap-1 text-sm text-gray-600 hover:text-indigo-600">
                <ArrowLeft className="w-4 h-4" />
                返回首页
              </Link>
            </div>
          </div>
          <div className="mt-4 bg-indigo-50 border border-indigo-200 rounded-lg p-3 flex items-start gap-2">
            <Info className="w-4 h-4 text-indigo-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-indigo-800">
              所有标的共用同一组均线类型/周期/资金/区间，保证横向可比。2 个标的时收益曲线默认双 Y 轴（左A右B），
              适合收益量级差距大时分别读数；3 个及以上自动用单轴归一化，并默认仅显示策略线（可开关显示持有线）。
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

          {/* 均线类型 */}
          <div>
            <label className="block text-sm text-gray-600 mb-2">均线类型</label>
            <div className="flex gap-2">
              {["SMA", "EMA"].map((t) => (
                <button
                  key={t}
                  onClick={() => setMaType(t)}
                  className={`px-4 py-2 rounded-lg text-sm border transition-colors ${
                    maType === t
                      ? "bg-indigo-600 text-white border-indigo-600"
                      : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  {t === "SMA" ? "SMA 简单均线" : "EMA 指数均线"}
                </button>
              ))}
            </div>
          </div>

          {/* 周期 */}
          <div>
            <label className="block text-sm text-gray-600 mb-2">均线周期（日）</label>
            <div className="flex flex-wrap gap-2 items-center">
              {PRESET_PERIODS.map((p) => (
                <button
                  key={p}
                  onClick={() => {
                    setPeriod(p);
                    setUseCustom(false);
                  }}
                  className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                    !useCustom && period === p
                      ? "bg-indigo-600 text-white border-indigo-600"
                      : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  {p}日
                </button>
              ))}
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setUseCustom(true)}
                  className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                    useCustom
                      ? "bg-indigo-600 text-white border-indigo-600"
                      : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  自定义
                </button>
                {useCustom && (
                  <input
                    type="number"
                    value={customPeriod}
                    onChange={(e) => setCustomPeriod(e.target.value)}
                    placeholder="周期"
                    min="2"
                    max="500"
                    className="w-20 border border-gray-300 rounded-lg px-2 py-1.5 text-sm"
                  />
                )}
              </div>
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
              className="flex items-center gap-1 text-sm px-3 py-1.5 rounded-lg border border-indigo-300 text-indigo-600 hover:bg-indigo-50 disabled:opacity-40 disabled:cursor-not-allowed"
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
                  activeSlot === i ? "border-indigo-400 ring-1 ring-indigo-200" : "border-gray-200"
                }`}
                onClick={() => setActiveSlot(i)}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className="inline-block w-3 h-3 rounded-full"
                    style={{ background: COLORS[i] }}
                  />
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
          {/* 自定义标的列表：点选填入当前激活槽位 */}
          <div>
            <p className="text-xs text-gray-500 mb-2">
              点击下方标的填入「标的 {String.fromCharCode(65 + activeSlot)}」（先点上方卡片切换目标槽位）
            </p>
            <CustomCodeList value={codes[activeSlot]} onSelect={(v) => setCodeAt(activeSlot, v)} />
          </div>

          <button
            onClick={handleRun}
            disabled={loading}
            className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 font-medium"
          >
            {loading ? "对比回测中..." : "开始对比回测"}
          </button>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{error}</div>
          )}
        </div>

        {/* 结果 */}
        {loading && (
          <div className="bg-white rounded-xl shadow-lg p-12 text-center text-gray-600">
            正在逐个回测对比标的，请稍候...
          </div>
        )}

        {validResults.length > 0 && !loading && (
          <>
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="font-semibold text-gray-900 mb-4">
                指标对比 · {maType}{effectivePeriod}日均线
              </h2>
              <CompareMetricsTable items={validResults} />
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="font-semibold text-gray-900 mb-4">累计收益曲线对比</h2>
              <CompareReturnChart series={validResults} />
            </div>

            {/* 各标的价格 + 均线 + 买卖点位走势图 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {validResults.map((it) => (
                <div key={it.code} className="bg-white rounded-xl shadow-lg p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="inline-block w-3 h-3 rounded-full" style={{ background: it.color }} />
                    <h2 className="font-semibold text-gray-900">
                      {it.name}（{it.code}） · 价格/均线/买卖点
                    </h2>
                  </div>
                  <CompareTradeChart
                    priceCurve={it.raw?.price_curve}
                    maCurve={it.raw?.ma_curve}
                    tradeRecords={it.raw?.trade_records}
                    maLabel={`${it.raw?.ma_config?.ma_type}${it.raw?.ma_config?.period}`}
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

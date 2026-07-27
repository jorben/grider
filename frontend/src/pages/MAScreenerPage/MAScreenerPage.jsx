import React, { useState, useCallback } from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  RefreshCw,
  Search,
  LineChart as LineChartIcon,
  Info,
} from "lucide-react";
import { runMAScreener } from "@shared/services/api";
import { useSortableData } from "@shared/hooks";
import { SortableTh } from "@shared/components/ui";

const CATEGORIES = ["全部", "宽基指数", "行业主题", "红利价值", "跨境海外", "商品能源"];
const PRESET_PERIODS = [5, 15, 20, 50, 99, 128, 225];

const pct = (v) => (typeof v === "number" ? (v * 100).toFixed(2) + "%" : "N/A");
const signColor = (v) => (typeof v === "number" ? (v > 0 ? "text-up-600" : v < 0 ? "text-down-600" : "text-gray-700") : "text-gray-400");

// 默认回测区间：2020-01-01 至今
const toYMD = (d) => d.toISOString().slice(0, 10);
const DEFAULT_START = "2020-01-01";
const DEFAULT_END = toYMD(new Date());

export default function MAScreenerPage() {
  const [maType, setMaType] = useState("SMA");
  const [period, setPeriod] = useState(20);
  const [customPeriod, setCustomPeriod] = useState("");
  const [useCustom, setUseCustom] = useState(false);
  const [startDate, setStartDate] = useState(DEFAULT_START);
  const [endDate, setEndDate] = useState(DEFAULT_END);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [category, setCategory] = useState("全部");
  const [hasRun, setHasRun] = useState(false);

  const effectivePeriod = useCustom ? parseInt(customPeriod, 10) : period;

  const handleRun = useCallback(
    async (forceRefresh = false) => {
      if (!effectivePeriod || effectivePeriod < 2 || effectivePeriod > 500) {
        setError("均线周期应在 2-500 之间");
        return;
      }
      setLoading(true);
      setError(null);
      setHasRun(true);
      try {
        const resp = await runMAScreener({
          period: effectivePeriod,
          maType,
          startDate: startDate || undefined,
          endDate: endDate || undefined,
          refresh: forceRefresh,
        });
        setData(resp.data);
      } catch (e) {
        setError(e.message || "筛选失败，请稍后重试");
      } finally {
        setLoading(false);
      }
    },
    [effectivePeriod, maType, startDate, endDate]
  );

  const results = data?.results || [];
  const filtered = category === "全部" ? results : results.filter((r) => r.category === category);
  // 默认按超额收益降序（与后端一致），表头可点击切换升/降序
  const { sorted, sortKey, sortDir, requestSort } = useSortableData(filtered, {
    key: "excess_return",
    dir: "desc",
  });

  return (
    <>
      <Helmet>
        <title>均线标的筛选器</title>
      </Helmet>

      <div className="space-y-6">
        {/* 标题 */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-100 rounded-lg">
                <LineChartIcon className="w-6 h-6 text-indigo-600" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">均线标的筛选器</h1>
                <p className="text-sm text-gray-600">
                  对主流 ETF 候选池用同一条均线回测，按超额收益排序，挑出适合均线交易的标的
                </p>
              </div>
            </div>
            <Link to="/" className="flex items-center gap-1 text-sm text-gray-600 hover:text-indigo-600">
              <ArrowLeft className="w-4 h-4" />
              返回首页
            </Link>
          </div>

          <div className="mt-4 bg-indigo-50 border border-indigo-200 rounded-lg p-3 flex items-start gap-2">
            <Info className="w-4 h-4 text-indigo-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-indigo-800">
              对约 50 只 ETF 各跑一遍近一年的均线回测，按「超额收益（策略 − 持有不动）」从高到低排序。
              超额为正说明在这只标的上用均线确实比躺着拿更划算。可切换周期/类型重新筛选。
            </p>
          </div>

          {/* 均线类型 + 周期选择 */}
          <div className="mt-4 space-y-3">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm text-gray-600 w-16">均线类型</span>
              {["SMA", "EMA"].map((t) => (
                <button
                  key={t}
                  onClick={() => setMaType(t)}
                  className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                    maType === t
                      ? "bg-indigo-600 text-white border-indigo-600"
                      : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm text-gray-600 w-16">均线周期</span>
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
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm text-gray-600 w-16">回测区间</span>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="border border-gray-300 rounded-lg px-2 py-1.5 text-sm"
              />
              <span className="text-gray-400 text-sm">至</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="border border-gray-300 rounded-lg px-2 py-1.5 text-sm"
              />
              <span className="text-xs text-gray-400">默认 2020-01-01 至今</span>
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="mt-4 flex items-center gap-3 flex-wrap">
            <button
              onClick={() => handleRun(false)}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors font-medium"
            >
              <Search className="w-4 h-4" />
              {loading ? "回测中..." : hasRun ? "重新筛选" : "开始筛选"}
            </button>
            {hasRun && !loading && (
              <button
                onClick={() => handleRun(true)}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm"
              >
                <RefreshCw className="w-4 h-4" />
                强制刷新数据
              </button>
            )}
            {data && (
              <span className="text-sm text-gray-500">
                {data.ma_config?.ma_type}{data.ma_config?.period}日 · 共 {data.total} 只 · 成功 {data.succeeded} · 失败{" "}
                {data.failed} · 耗时 {data.elapsed_seconds ?? "-"}s · 更新于 {data.generated_at}
                {data.from_cache ? "（缓存）" : ""}
              </span>
            )}
          </div>
        </div>

        {loading && (
          <div className="bg-white rounded-xl shadow-lg p-12 text-center">
            <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto mb-4" />
            <p className="text-gray-600">
              正在对候选池逐只回测（约需 40~60 秒，受数据源速度影响）...
            </p>
          </div>
        )}

        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {!loading && data && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center gap-2 mb-4 flex-wrap">
              {CATEGORIES.map((c) => (
                <button
                  key={c}
                  onClick={() => setCategory(c)}
                  className={`px-3 py-1 rounded-full text-sm transition-colors ${
                    category === c
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-gray-500 text-left">
                    <th className="py-3 px-2">排名</th>
                    <th className="py-3 px-2">代码</th>
                    <th className="py-3 px-2">名称</th>
                    <SortableTh label="超额收益" sortKey="excess_return" activeKey={sortKey} dir={sortDir} onSort={requestSort} />
                    <SortableTh label="策略收益" sortKey="total_return" activeKey={sortKey} dir={sortDir} onSort={requestSort} />
                    <SortableTh label="持有收益" sortKey="hold_return" activeKey={sortKey} dir={sortDir} onSort={requestSort} />
                    <SortableTh label="盈亏比" sortKey="profit_loss_ratio" activeKey={sortKey} dir={sortDir} onSort={requestSort} />
                    <SortableTh label="夏普比率" sortKey="sharpe_ratio" activeKey={sortKey} dir={sortDir} onSort={requestSort} />
                    <SortableTh label="最大回撤" sortKey="max_drawdown" activeKey={sortKey} dir={sortDir} onSort={requestSort} />
                    <SortableTh label="最近交易时间" sortKey="last_trade_date" activeKey={sortKey} dir={sortDir} onSort={requestSort} />
                    <SortableTh label="胜率" sortKey="win_rate" activeKey={sortKey} dir={sortDir} onSort={requestSort} />
                    <th className="py-3 px-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {sorted.map((r, idx) => (
                    <tr key={r.code + idx} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-2 text-gray-400">{idx + 1}</td>
                      <td className="py-3 px-2 font-medium text-gray-900">{r.code}</td>
                      <td className="py-3 px-2 text-gray-700">{r.name}</td>
                      {r.excess_return === null || r.excess_return === undefined ? (
                        <td className="py-3 px-2 text-right text-red-400" colSpan={8}>
                          数据获取失败
                        </td>
                      ) : (
                        <>
                          <td className={`py-3 px-2 text-right font-bold ${signColor(r.excess_return)}`}>
                            {pct(r.excess_return)}
                          </td>
                          <td className={`py-3 px-2 text-right ${signColor(r.total_return)}`}>{pct(r.total_return)}</td>
                          <td className={`py-3 px-2 text-right ${signColor(r.hold_return)}`}>{pct(r.hold_return)}</td>
                          <td className="py-3 px-2 text-right text-gray-600">
                            {typeof r.profit_loss_ratio === "number" ? r.profit_loss_ratio.toFixed(2) : "—"}
                          </td>
                          <td className="py-3 px-2 text-right text-gray-600">
                            {typeof r.sharpe_ratio === "number" ? r.sharpe_ratio.toFixed(2) : "—"}
                          </td>
                          <td className="py-3 px-2 text-right text-down-600">{pct(r.max_drawdown)}</td>
                          <td className="py-3 px-2 text-right text-gray-600 whitespace-nowrap">{r.last_trade_date || "—"}</td>
                          <td className="py-3 px-2 text-right text-gray-600">{pct(r.win_rate)}</td>
                        </>
                      )}
                      <td className="py-3 px-2">
                        <a
                          href={`/ma-backtest?code=${r.code}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-indigo-600 hover:text-indigo-700 text-xs whitespace-nowrap"
                        >
                          more
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {sorted.length === 0 && <p className="text-center text-gray-500 py-8">该分类下暂无标的</p>}
            </div>
          </div>
        )}

        {!loading && !data && !error && (
          <div className="bg-white rounded-xl shadow-lg p-12 text-center">
            <LineChartIcon className="w-10 h-10 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">
              选好均线类型与周期后点击「开始筛选」，系统会对约 50 只主流 ETF 逐一回测并按超额收益排序
            </p>
          </div>
        )}
      </div>
    </>
  );
}

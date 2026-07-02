import React, { useState, useEffect, useCallback } from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { ArrowLeft, Waves, Info, RefreshCw } from "lucide-react";
import { runFishBasin } from "@shared/services/api";
import { useSortableData } from "@shared/hooks/useSortableData";
import SortableTh from "@shared/components/ui/SortableTh";

const pct = (v) => (typeof v === "number" ? (v * 100).toFixed(2) + "%" : "—");
const signedPct = (v) => (typeof v === "number" ? (v >= 0 ? "+" : "") + (v * 100).toFixed(2) + "%" : "—");
const intFmt = (v) => (typeof v === "number" ? v.toLocaleString("en-US") : "—");

// 偏离率背景色：正=红渐变(越强越红)，负=绿渐变(越弱越绿)
const devBg = (v) => {
  if (typeof v !== "number") return "";
  const a = Math.min(Math.abs(v) / 0.12, 1); // 12% 封顶
  if (v > 0) return `rgba(239,68,68,${0.12 + a * 0.5})`;
  if (v < 0) return `rgba(16,185,129,${0.12 + a * 0.5})`;
  return "";
};

// 排序变化箭头：正=上升(变强)红，负=下降绿
const RankChange = ({ v }) => {
  if (typeof v !== "number" || v === 0) return <span className="text-gray-400">0</span>;
  if (v > 0) return <span className="text-red-600 font-medium">↑{v}</span>;
  return <span className="text-green-600 font-medium">↓{Math.abs(v)}</span>;
};

const STATE_STYLE = {
  bull: { bg: "from-red-50 to-rose-100", text: "text-red-700", dot: "bg-red-500", label: "牛市状态" },
  bear: { bg: "from-green-50 to-emerald-100", text: "text-green-700", dot: "bg-green-500", label: "熊市状态" },
  mixed: { bg: "from-amber-50 to-yellow-100", text: "text-amber-700", dot: "bg-amber-500", label: "分化 / 震荡" },
  neutral: { bg: "from-gray-50 to-gray-100", text: "text-gray-700", dot: "bg-gray-400", label: "未知" },
};

export default function FishBasinPage() {
  const [board, setBoard] = useState("index"); // index=大盘指数, sector=板块轮动
  const [buffer, setBuffer] = useState(0);
  const [dataMap, setDataMap] = useState({}); // { index: payload, sector: payload }
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const data = dataMap[board] || null;

  const load = useCallback(async (opts = {}) => {
    const b = opts.board || board;
    setLoading(true);
    setError(null);
    try {
      const resp = await runFishBasin({ buffer, board: b, ...opts });
      setDataMap((prev) => ({ ...prev, [b]: resp.data }));
    } catch (e) {
      setError(e.message || "加载失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  }, [buffer, board]);

  // 首次加载大盘指数
  useEffect(() => {
    load({ board: "index" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 切换 Tab 时若该板块还没数据则拉取
  const switchBoard = (b) => {
    setBoard(b);
    if (!dataMap[b]) load({ board: b });
  };

  const results = data?.results || [];
  const { sorted, sortKey, sortDir, requestSort } = useSortableData(results, {
    key: "deviation",
    dir: "desc",
  });

  const ms = data?.market_state;
  const style = STATE_STYLE[ms?.tone] || STATE_STYLE.neutral;

  return (
    <>
      <Helmet>
        <title>鱼盆模型 · 市场风向标</title>
      </Helmet>

      <div className="space-y-6">
        {/* 标题 */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-sky-100 rounded-lg">
                <Waves className="w-6 h-6 text-sky-600" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">鱼盆模型 · 市场风向标</h1>
                <p className="text-sm text-gray-600">
                  以 20 日线为临界值，判断主流指数强弱，勾勒市场"大势"
                </p>
              </div>
            </div>
            <Link to="/" className="flex items-center gap-1 text-sm text-gray-600 hover:text-sky-600">
              <ArrowLeft className="w-4 h-4" />
              返回首页
            </Link>
          </div>
          <div className="mt-4 bg-sky-50 border border-sky-200 rounded-lg p-3 flex items-start gap-2">
            <Info className="w-4 h-4 text-sky-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-sky-800">
              鱼盆模型用于判断市场大势强弱：收盘价 ≥ 临界值为 YES（偏强），&lt; 临界值为 NO（偏弱）。
              <b>YES/NO 仅代表指数相对 20 日线的强弱，非买卖信号。</b>
              全部 YES 通常对应"牛市状态"，全部 NO 对应"熊市状态"，遵循"去弱留强"。
            </p>
          </div>
        </div>

        {/* Tab 切换：大盘指数 / 板块轮动 */}
        <div className="bg-white rounded-xl shadow-lg p-2 flex gap-2">
          {[
            { id: "index", label: "大盘指数" },
            { id: "sector", label: "板块轮动" },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => switchBoard(t.id)}
              className={`flex-1 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                board === t.id
                  ? "bg-sky-600 text-white"
                  : "bg-white text-gray-600 hover:bg-gray-50"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* 市场状态横幅 */}
        {ms && (
          <div className={`bg-gradient-to-r ${style.bg} rounded-xl shadow-lg p-6`}>
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-3">
                <span className={`inline-block w-4 h-4 rounded-full ${style.dot}`} />
                <div>
                  <div className={`text-2xl font-bold ${style.text}`}>{style.label}</div>
                  <div className="text-sm text-gray-600 mt-1">
                    {ms.total > 0 ? `${ms.yes}/${ms.total} 个${board === "sector" ? "板块" : "指数"}处于 YES（站上临界值）` : "暂无数据"}
                  </div>
                </div>
              </div>
              <div className="text-xs text-gray-500">
                {typeof data?.realtime_count === "number" && data.realtime_count > 0
                  ? `实时 ${data.realtime_count} 项，其余为收盘 · `
                  : ""}
                更新于 {data?.generated_at}
                {data?.from_cache ? "（缓存）" : ""}
              </div>
            </div>
          </div>
        )}

        {/* 控制栏 */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-end gap-4 flex-wrap">
            <div>
              <label className="block text-sm text-gray-600 mb-1">临界值浮动（%）</label>
              <input
                type="number"
                value={buffer}
                onChange={(e) => setBuffer(parseFloat(e.target.value) || 0)}
                step="0.5"
                min="-5"
                max="5"
                className="w-32 border border-gray-300 rounded-lg px-3 py-2"
              />
              <p className="text-xs text-gray-500 mt-1">
                0 = 纯 20 日线；填 2 表示临界值 = 20日线 × 1.02（更需站稳才算 YES）
              </p>
            </div>
            <button
              onClick={() => load()}
              disabled={loading}
              className="px-5 py-2.5 bg-sky-600 text-white rounded-lg hover:bg-sky-700 disabled:opacity-50 font-medium"
            >
              {loading ? "计算中..." : "刷新"}
            </button>
            <button
              onClick={() => load({ refresh: 1 })}
              disabled={loading}
              className="flex items-center gap-1 px-4 py-2.5 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              title="忽略缓存，重新拉取所有标的最新行情"
            >
              <RefreshCw className="w-4 h-4" />
              强制更新数据
            </button>
          </div>
          {error && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{error}</div>
          )}
        </div>

        {/* 表格 */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          {loading && (!data) ? (
            <div className="py-12 text-center text-gray-500">正在计算各指数临界值...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-gray-500 text-left">
                    <SortableTh label="排序" sortKey="strength" activeKey={sortKey} dir={sortDir} onSort={requestSort} align="left" />
                    <th className="py-2 px-2">代码</th>
                    <th className="py-2 px-2">名称</th>
                    <SortableTh label="涨幅%" sortKey="change_pct" activeKey={sortKey} dir={sortDir} onSort={requestSort} align="left" />
                    <SortableTh label="现价" sortKey="price" activeKey={sortKey} dir={sortDir} onSort={requestSort} align="left" />
                    <SortableTh label="20日线" sortKey="ma20" activeKey={sortKey} dir={sortDir} onSort={requestSort} align="left" />
                    <SortableTh label="偏离率" sortKey="deviation" activeKey={sortKey} dir={sortDir} onSort={requestSort} align="left" />
                    <SortableTh label="量比" sortKey="vol_ratio" activeKey={sortKey} dir={sortDir} onSort={requestSort} align="left" />
                    <th className="py-2 px-2 text-left">状态</th>
                    <SortableTh label="状态转变" sortKey="status_since" activeKey={sortKey} dir={sortDir} onSort={requestSort} align="left" />
                    <SortableTh label="区间涨幅%" sortKey="range_pct" activeKey={sortKey} dir={sortDir} onSort={requestSort} align="left" />
                    <SortableTh label="排序变化" sortKey="rank_change" activeKey={sortKey} dir={sortDir} onSort={requestSort} align="left" />
                    <SortableTh label="数据时间" sortKey="data_time" activeKey={sortKey} dir={sortDir} onSort={requestSort} align="left" />
                  </tr>
                </thead>
                <tbody>
                  {sorted.map((r) => (
                    <tr key={r.code} className="border-b border-gray-100">
                      <td className="py-2 px-2">
                        {r.strength != null ? (
                          <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                            r.strength === 1 ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-600"
                          }`}>
                            {r.strength}
                          </span>
                        ) : "—"}
                      </td>
                      <td className="py-2 px-2 text-gray-500">{r.code}</td>
                      <td className="py-2 px-2 font-medium text-gray-900">{r.name}</td>
                      <td className={`py-2 px-2 text-left ${
                        typeof r.change_pct === "number" ? (r.change_pct > 0 ? "text-up-600" : r.change_pct < 0 ? "text-down-600" : "") : ""
                      }`}>{signedPct(r.change_pct)}</td>
                      <td className="py-2 px-2 text-left">{intFmt(r.price)}</td>
                      <td className="py-2 px-2 text-left text-gray-600">{intFmt(r.ma20)}</td>
                      <td className="py-2 px-2 text-left font-medium" style={{ background: devBg(r.deviation) }}>{signedPct(r.deviation)}</td>
                      <td className="py-2 px-2 text-left text-gray-600">{typeof r.vol_ratio === "number" ? r.vol_ratio.toFixed(2) : "—"}</td>
                      <td className="py-2 px-2 text-left">
                        {r.status === "YES" && (
                          <span className="px-2 py-0.5 rounded-full bg-red-100 text-red-700 text-xs font-bold">YES</span>
                        )}
                        {r.status === "NO" && (
                          <span className="px-2 py-0.5 rounded-full bg-green-100 text-green-700 text-xs font-bold">NO</span>
                        )}
                        {!r.status && <span className="text-gray-400 text-xs">失败</span>}
                      </td>
                      <td className="py-2 px-2 text-gray-500 whitespace-nowrap">{r.status_since || "—"}</td>
                      <td className={`py-2 px-2 text-left ${
                        typeof r.range_pct === "number" ? (r.range_pct > 0 ? "text-up-600" : r.range_pct < 0 ? "text-down-600" : "") : ""
                      }`}>{signedPct(r.range_pct)}</td>
                      <td className="py-2 px-2 text-left"><RankChange v={r.rank_change} /></td>
                      <td className="py-2 px-2 text-left whitespace-nowrap text-xs text-gray-500">
                        {r.data_time || r.latest_date || "—"}
                        {r.is_realtime && <span className="text-emerald-500 ml-1" title="盘中实时">●</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-xs text-gray-500 mt-3">
                排序按偏离率从高到低（1=偏离率最高/最强）。临界值 = 20日均线 ×(1+浮动%)；现价/临界/20日线均取整。
                偏离率底色：红=强(站上线)、绿=弱(跌破线)。量比=当日量÷近5日均量（商品现货无量显示—）。
                区间涨幅=本轮状态起点至今涨跌。排序变化=较上次刷新的名次升降。
                数据时间带 ● 为盘中实时(精确到秒，A股指数/港股/COMEX)，其余为最近收盘日期(美股及中证行业指数无实时源)。
                {data?.elapsed_seconds != null && ` 本次计算耗时 ${data.elapsed_seconds}s。`}
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

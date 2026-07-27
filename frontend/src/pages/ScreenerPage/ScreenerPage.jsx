import React, { useState, useCallback } from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  RefreshCw,
  Search,
  TrendingUp,
  Filter,
  Info,
} from "lucide-react";
import { runScreener } from "@shared/services/api";
import { useSortableData } from "@shared/hooks";
import { SortableTh } from "@shared/components/ui";

// 分类筛选选项
const CATEGORIES = ["全部", "宽基指数", "行业主题", "红利价值", "跨境海外", "商品能源"];

// 结论对应的样式
const conclusionStyle = (conclusion) => {
  switch (conclusion) {
    case "非常适合":
      return "bg-green-100 text-green-700";
    case "基本适合":
      return "bg-yellow-100 text-yellow-700";
    case "不适合":
      return "bg-gray-100 text-gray-600";
    default:
      return "bg-red-100 text-red-700"; // 存在严重缺陷
  }
};

// 分数对应的颜色
const scoreColor = (score) => {
  if (score >= 70) return "text-green-600";
  if (score >= 60) return "text-yellow-600";
  return "text-red-500";
};

export default function ScreenerPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [category, setCategory] = useState("全部");
  const [hasRun, setHasRun] = useState(false);

  const handleRun = useCallback(async (forceRefresh = false) => {
    setLoading(true);
    setError(null);
    setHasRun(true);
    try {
      const resp = await runScreener(forceRefresh);
      setData(resp.data);
    } catch (e) {
      setError(e.message || "筛选失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  }, []);

  const results = data?.results || [];
  const filtered =
    category === "全部"
      ? results
      : results.filter((r) => r.category === category);
  // 默认按总分降序，表头可点击切换升/降序
  const { sorted, sortKey, sortDir, requestSort } = useSortableData(filtered, {
    key: "total_score",
    dir: "desc",
  });

  return (
    <>
      <Helmet>
        <title>网格标的筛选器</title>
      </Helmet>

      <div className="space-y-6">
        {/* 顶部标题与返回 */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Filter className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">网格标的筛选器</h1>
                <p className="text-sm text-gray-600">
                  对主流 ETF 候选池按适宜度评分排序，快速挑出适合网格交易的标的
                </p>
              </div>
            </div>
            <Link
              to="/"
              className="flex items-center gap-1 text-sm text-gray-600 hover:text-blue-600"
            >
              <ArrowLeft className="w-4 h-4" />
              返回首页
            </Link>
          </div>

          {/* 评分说明 */}
          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start gap-2">
            <Info className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-blue-800">
              评分维度：振幅 ATR(35) + 波动率(30) + 市场特征 ADX(25) + 流动性(10) = 100 分。
              ≥70 非常适合 / 60~70 基本适合 / &lt;60 不适合。点击任意标的可跳转到详细分析。
            </p>
          </div>

          {/* 操作按钮 */}
          <div className="mt-4 flex items-center gap-3 flex-wrap">
            <button
              onClick={() => handleRun(false)}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors font-medium"
            >
              <Search className="w-4 h-4" />
              {loading ? "评分中..." : hasRun ? "重新筛选" : "开始筛选"}
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
                共 {data.total} 只 · 成功 {data.succeeded} · 失败 {data.failed} · 耗时{" "}
                {data.elapsed_seconds ?? "-"}s · 更新于 {data.generated_at}
                {data.from_cache ? "（缓存）" : ""}
              </span>
            )}
          </div>
        </div>

        {/* 加载提示 */}
        {loading && (
          <div className="bg-white rounded-xl shadow-lg p-12 text-center">
            <RefreshCw className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-4" />
            <p className="text-gray-600">
              正在批量评估候选池（约需 10~30 秒，受数据源速度影响）...
            </p>
          </div>
        )}

        {/* 错误提示 */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* 结果表格 */}
        {!loading && data && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            {/* 分类筛选 */}
            <div className="flex items-center gap-2 mb-4 flex-wrap">
              {CATEGORIES.map((c) => (
                <button
                  key={c}
                  onClick={() => setCategory(c)}
                  className={`px-3 py-1 rounded-full text-sm transition-colors ${
                    category === c
                      ? "bg-blue-600 text-white"
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
                    <th className="py-3 px-2">分类</th>
                    <SortableTh label="总分" sortKey="total_score" activeKey={sortKey} dir={sortDir} onSort={requestSort} />
                    <SortableTh label="振幅ATR%" sortKey="atr_pct" activeKey={sortKey} dir={sortDir} onSort={requestSort} />
                    <SortableTh label="波动率%" sortKey="volatility_pct" activeKey={sortKey} dir={sortDir} onSort={requestSort} />
                    <SortableTh label="ADX" sortKey="adx_value" activeKey={sortKey} dir={sortDir} onSort={requestSort} />
                    <SortableTh label="日均成交额(万)" sortKey="avg_amount" activeKey={sortKey} dir={sortDir} onSort={requestSort} />
                    <SortableTh label="结论" sortKey="total_score" activeKey={sortKey} dir={sortDir} onSort={requestSort} align="left" />
                    <th className="py-3 px-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {sorted.map((r, idx) => (
                    <tr
                      key={r.code + idx}
                      className="border-b border-gray-100 hover:bg-gray-50"
                    >
                      <td className="py-3 px-2 text-gray-400">{idx + 1}</td>
                      <td className="py-3 px-2 font-medium text-gray-900">{r.code}</td>
                      <td className="py-3 px-2 text-gray-700">{r.name}</td>
                      <td className="py-3 px-2 text-gray-500">{r.category}</td>
                      {r.total_score === null ? (
                        <td className="py-3 px-2 text-right text-red-400" colSpan={6}>
                          数据获取失败
                        </td>
                      ) : (
                        <>
                          <td className={`py-3 px-2 text-right font-bold ${scoreColor(r.total_score)}`}>
                            {r.total_score}
                          </td>
                          <td className="py-3 px-2 text-right text-gray-600">{r.atr_pct}</td>
                          <td className="py-3 px-2 text-right text-gray-600">{r.volatility_pct}</td>
                          <td className="py-3 px-2 text-right text-gray-600">{r.adx_value}</td>
                          <td className="py-3 px-2 text-right text-gray-600">
                            {r.avg_amount?.toLocaleString()}
                          </td>
                          <td className="py-3 px-2">
                            <span className={`px-2 py-0.5 rounded-full text-xs ${conclusionStyle(r.conclusion)}`}>
                              {r.conclusion}
                            </span>
                          </td>
                        </>
                      )}
                      <td className="py-3 px-2">
                        <Link
                          to={`/analysis/${r.code}?capital=100000&grid=geometric&risk=balanced&adjustment=1.0`}
                          className="flex items-center gap-1 text-blue-600 hover:text-blue-700 text-xs whitespace-nowrap"
                        >
                          <TrendingUp className="w-3 h-3" />
                          分析
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {sorted.length === 0 && (
                <p className="text-center text-gray-500 py-8">该分类下暂无标的</p>
              )}
            </div>
          </div>
        )}

        {/* 初始空状态 */}
        {!loading && !data && !error && (
          <div className="bg-white rounded-xl shadow-lg p-12 text-center">
            <Filter className="w-10 h-10 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">
              点击「开始筛选」，系统会对约 50 只主流 ETF 逐一评分并按适宜度排序
            </p>
          </div>
        )}
      </div>
    </>
  );
}

import React, { useState, useCallback } from "react";
import { Helmet } from "react-helmet-async";
import { Link, useSearchParams } from "react-router-dom";
import {
  ArrowLeft,
  LineChart as LineChartIcon,
  Info,
  TrendingUp,
  Download,
} from "lucide-react";
import * as XLSX from "xlsx";
import { runMABacktest } from "@shared/services/api";
import MABacktestChart from "./MABacktestChart";
import CustomCodeList from "@features/etf/components/CustomCodeList";

// 常用均线周期
const PRESET_PERIODS = [5, 15, 20, 50, 99, 128, 225];

const pct = (v) => (typeof v === "number" ? (v * 100).toFixed(2) + "%" : "N/A");

// 计算默认回测区间：2020-01-01 至今
const toYMD = (d) => d.toISOString().slice(0, 10);
const DEFAULT_END = toYMD(new Date());
const DEFAULT_START = "2020-01-01";

export default function MABacktestPage() {
  const [searchParams] = useSearchParams();
  // 从 URL 读取初始代码（如从均线筛选器「详细回测」跳转带入），默认 510300
  const initialCode = (searchParams.get("code") || "510300").replace(/[^0-9a-zA-Z]/g, "").toUpperCase();
  const [code, setCode] = useState(initialCode);
  const [capital, setCapital] = useState(100000);
  const [maType, setMaType] = useState("SMA");
  const [period, setPeriod] = useState(20);
  const [customPeriod, setCustomPeriod] = useState("");
  const [useCustom, setUseCustom] = useState(false);
  const [startDate, setStartDate] = useState(DEFAULT_START);
  const [endDate, setEndDate] = useState(DEFAULT_END);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const effectivePeriod = useCustom ? parseInt(customPeriod, 10) : period;

  const handleRun = useCallback(async () => {
    setError(null);
    if (!code.trim()) {
      setError("请输入标的代码");
      return;
    }
    if (!effectivePeriod || effectivePeriod < 2 || effectivePeriod > 500) {
      setError("均线周期应在 2-500 之间");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const resp = await runMABacktest({
        etfCode: code.trim(),
        totalCapital: Number(capital),
        maParams: {
          period: effectivePeriod,
          maType,
        },
        startDate: startDate || undefined,
        endDate: endDate || undefined,
      });
      setResult(resp.data);
    } catch (e) {
      setError(e.message || "回测失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  }, [code, capital, maType, effectivePeriod, startDate, endDate]);

  // 导出交易记录为 Excel（.xlsx）
  const handleExportExcel = useCallback(() => {
    const records = result?.trade_records || [];
    if (records.length === 0) return;
    try {
      const exportData = records.map((t, i) => ({
        "序号": i + 1,
        "时间": t.time,
        "方向": t.type === "BUY" ? "买入" : "卖出",
        "价格": typeof t.price === "number" ? Number(t.price.toFixed(3)) : t.price,
        "数量": t.quantity,
        "手续费": typeof t.commission === "number" ? Number(t.commission.toFixed(2)) : t.commission,
        "持仓": t.position,
        "现金": t.cash,
      }));
      const wb = XLSX.utils.book_new();
      const ws = XLSX.utils.json_to_sheet(exportData, {
        header: ["序号", "时间", "方向", "价格", "数量", "手续费", "持仓", "现金"],
      });
      ws["!cols"] = [
        { wch: 8 }, { wch: 20 }, { wch: 8 }, { wch: 12 },
        { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 15 },
      ];
      XLSX.utils.book_append_sheet(wb, ws, "交易记录");
      const maLabel = `${result?.ma_config?.ma_type || maType}${result?.ma_config?.period || period}`;
      const timestamp = new Date().toISOString().slice(0, 19).replace(/[:]/g, "-");
      XLSX.writeFile(wb, `均线交易记录_${code}_${maLabel}_${timestamp}.xlsx`);
    } catch (e) {
      console.error("导出Excel失败:", e);
      alert("导出Excel失败，请稍后重试");
    }
  }, [result, code, maType, period]);

  const m = result?.performance_metrics;
  const tm = result?.trading_metrics;
  const bm = result?.benchmark_comparison;

  return (
    <>
      <Helmet>
        <title>均线策略回测</title>
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
                <h1 className="text-xl font-bold text-gray-900">均线策略回测</h1>
                <p className="text-sm text-gray-600">
                  趋势跟随策略：价格上穿均线买入，下穿均线清仓
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Link to="/ma-compare" className="text-sm text-indigo-600 hover:text-indigo-700 font-medium">
                多标的对比
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
              均线策略与网格策略相反：网格适合震荡行情（低买高卖），均线适合趋势行情（追涨杀跌）。
              收盘价上穿所选均线视为金叉买入，下穿视为死叉清仓。
            </p>
          </div>
        </div>

        {/* 参数设置 */}
        <div className="bg-white rounded-xl shadow-lg p-6 space-y-5">
          <h2 className="font-semibold text-gray-900">策略参数</h2>

          {/* 标的 + 资金 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">标的代码</label>
              <input
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/[^0-9a-zA-Z]/g, "").toUpperCase())}
                placeholder="如：510300、603137"
                maxLength={6}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>
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
          </div>

          {/* 自定义标的（独占整行，容纳更多代码再换行） */}
          <CustomCodeList value={code} onSelect={setCode} />

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

          {/* 均线周期 */}
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

          {/* 回测区间（可选） */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">开始日期（可选）</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">结束日期（可选）</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>
          </div>
          <p className="text-xs text-gray-500 -mt-2">默认回测 2020-01-01 至今（已预填，可自行调整）。长周期均线（如128/225日）会自动往前取预热数据，无需手动拉长区间。跨度超过120天自动使用日线。</p>

          <button
            onClick={handleRun}
            disabled={loading}
            className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 font-medium"
          >
            {loading ? "回测中..." : "开始回测"}
          </button>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{error}</div>
          )}
        </div>

        {/* 结果 */}
        {loading && (
          <div className="bg-white rounded-xl shadow-lg p-12 text-center text-gray-600">
            正在回测，请稍候...
          </div>
        )}

        {result && !loading && (
          <>
            {/* 指标概览 */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
                <h2 className="font-semibold text-gray-900">
                  {result.etf_info?.name}（{result.etf_info?.code}） · {result.ma_config?.ma_type}
                  {result.ma_config?.period}日均线
                </h2>
                <span className="text-sm text-gray-500">
                  {result.backtest_period?.start_date} ~ {result.backtest_period?.end_date}
                  （{result.backtest_period?.trading_days}个交易日）
                </span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <Metric label="策略总收益" value={pct(m?.total_return)} positive={m?.total_return} />
                <Metric label="持有不动收益" value={pct(bm?.hold_return)} positive={bm?.hold_return} />
                <Metric label="超额收益" value={pct(bm?.excess_return)} positive={bm?.excess_return} />
                <Metric label="年化收益" value={pct(m?.annualized_return)} positive={m?.annualized_return} />
                <Metric label="最大回撤" value={pct(m?.max_drawdown)} positive={0} />
                <Metric label="夏普比率" value={m?.sharpe_ratio != null ? m.sharpe_ratio.toFixed(2) : "N/A"} />
                <Metric label="盈亏比" value={tm?.profit_loss_ratio != null ? tm.profit_loss_ratio.toFixed(2) : "N/A"} />
                <Metric label="交易次数" value={`${tm?.sell_trades ?? 0} 次（买${tm?.buy_trades}/卖${tm?.sell_trades}）`} />
                <Metric label="胜率" value={pct(tm?.win_rate)} />
              </div>
            </div>

            {/* 图表 */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-5 h-5 text-indigo-600" />
                <h2 className="font-semibold text-gray-900">价格 / 均线 / 买卖点</h2>
              </div>
              <MABacktestChart
                priceCurve={result.price_curve}
                maCurve={result.ma_curve}
                tradeRecords={result.trade_records}
                maLabel={`${result.ma_config?.ma_type}${result.ma_config?.period}`}
              />
            </div>

            {/* 交易记录 */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-gray-900">交易记录（{result.trade_records?.length || 0} 笔）</h2>
                <button
                  onClick={handleExportExcel}
                  disabled={!result.trade_records || result.trade_records.length === 0}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                  title="导出Excel文件"
                >
                  <Download className="w-4 h-4" />
                  导出
                </button>
              </div>
              <div className="overflow-x-auto max-h-96 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-white">
                    <tr className="border-b border-gray-200 text-gray-500 text-left">
                      <th className="py-2 px-2">时间</th>
                      <th className="py-2 px-2">方向</th>
                      <th className="py-2 px-2 text-right">价格</th>
                      <th className="py-2 px-2 text-right">数量</th>
                      <th className="py-2 px-2 text-right">手续费</th>
                      <th className="py-2 px-2 text-right">持仓</th>
                      <th className="py-2 px-2 text-right">现金</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.trade_records?.map((t, i) => (
                      <tr key={i} className="border-b border-gray-100">
                        <td className="py-2 px-2 text-gray-600">{t.time}</td>
                        <td className="py-2 px-2">
                          <span className={t.type === "BUY" ? "text-up-600" : "text-down-600"}>
                            {t.type === "BUY" ? "买入" : "卖出"}
                          </span>
                        </td>
                        <td className="py-2 px-2 text-right">{t.price?.toFixed(3)}</td>
                        <td className="py-2 px-2 text-right">{t.quantity}</td>
                        <td className="py-2 px-2 text-right text-gray-500">{t.commission?.toFixed(2)}</td>
                        <td className="py-2 px-2 text-right">{t.position}</td>
                        <td className="py-2 px-2 text-right text-gray-500">{t.cash?.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {(!result.trade_records || result.trade_records.length === 0) && (
                  <p className="text-center text-gray-500 py-8">该区间内未触发任何买卖信号</p>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
}

function Metric({ label, value, positive }) {
  let color = "text-gray-900";
  if (typeof positive === "number") {
    color = positive > 0 ? "text-up-600" : positive < 0 ? "text-down-600" : "text-gray-900";
  }
  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-lg font-bold ${color}`}>{value}</p>
    </div>
  );
}

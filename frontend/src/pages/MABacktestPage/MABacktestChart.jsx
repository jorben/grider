import React, { useMemo } from "react";
import {
  ComposedChart,
  Line,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

/**
 * 均线回测图表：价格折线 + 均线折线 + 买卖点散点
 */
export default function MABacktestChart({ priceCurve = [], maCurve = [], tradeRecords = [], maLabel = "MA" }) {
  // 抽样，避免点过多
  const sample = (arr, max = 2400) => {
    if (arr.length <= max) return arr;
    const step = Math.ceil(arr.length / max);
    return arr.filter((_, i) => i % step === 0);
  };

  const data = useMemo(() => {
    // 以时间为键合并 ma 和买卖点
    const maMap = new Map(maCurve.map((p) => [p.time, p.ma]));
    const buyMap = new Map();
    const sellMap = new Map();
    tradeRecords.forEach((t) => {
      if (t.type === "BUY") buyMap.set(t.time, t.price);
      else sellMap.set(t.time, t.price);
    });

    const merged = priceCurve.map((bar) => {
      const dt = new Date(bar.time);
      // 日线回测：时间戳为当日 15:00，分钟无意义，tooltip 只显示到「日」
      const isDailyClose = dt.getHours() === 15 && dt.getMinutes() === 0;
      const fullTime = isDailyClose
        ? dt.toLocaleDateString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit" })
        : dt.toLocaleString("zh-CN", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
          });
      return {
        time: dt.toLocaleDateString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit" }),
        fullTime,
        close: bar.close,
        ma: maMap.get(bar.time) ?? null,
        buyPrice: buyMap.get(bar.time) ?? null,
        sellPrice: sellMap.get(bar.time) ?? null,
      };
    });
    return sample(merged);
  }, [priceCurve, maCurve, tradeRecords]);

  return (
    <ResponsiveContainer width="100%" height={420}>
      <ComposedChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis
          dataKey="time"
          tick={{ fontSize: 12 }}
          interval="preserveStartEnd"
          tickFormatter={(v) => (typeof v === "string" ? v.slice(5) : v)}
        />
        <YAxis
          domain={["dataMin - 0.1", "dataMax + 0.1"]}
          tick={{ fontSize: 12 }}
          tickFormatter={(v) => v.toFixed(3)}
        />
        <Tooltip
          content={({ active, payload }) => {
            if (active && payload && payload.length) {
              const d = payload[0].payload;
              return (
                <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
                  <p className="text-sm font-semibold text-gray-900 mb-2">{d.fullTime}</p>
                  <div className="space-y-1 text-sm">
                    <p className="text-gray-700">价格: <span className="font-medium">{d.close?.toFixed(3)}</span></p>
                    {d.ma != null && (
                      <p className="text-amber-600">{maLabel}: <span className="font-medium">{d.ma.toFixed(3)}</span></p>
                    )}
                    {d.buyPrice && <p className="text-up-600 font-medium">↑ 买入: {d.buyPrice.toFixed(3)}</p>}
                    {d.sellPrice && <p className="text-down-600 font-medium">↓ 卖出: {d.sellPrice.toFixed(3)}</p>}
                  </div>
                </div>
              );
            }
            return null;
          }}
        />
        <Legend />
        <Line type="monotone" dataKey="close" stroke="#6f7784" strokeWidth={2} dot={false} name="价格" />
        <Line type="monotone" dataKey="ma" stroke="#f59e0b" strokeWidth={2} dot={false} name={maLabel} connectNulls />
        <Scatter dataKey="buyPrice" fill="#ef4444" shape="circle" name="买入" />
        <Scatter dataKey="sellPrice" fill="#3b82f6" shape="circle" name="卖出" />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

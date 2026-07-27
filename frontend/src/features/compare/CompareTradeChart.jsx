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
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";

/**
 * 单标的「价格 + 交易点位」走势图（对比页每个标的各一张，与单标的分析口径一致）。
 *
 * props:
 *   priceCurve: [{ time, close, high, low }]
 *   tradeRecords: [{ time, type:'BUY'|'SELL', price }]
 *   maCurve: [{ time, ma }]            可选（均线策略传入）
 *   maLabel: string                    可选（均线标签，如 "SMA20"）
 *   gridRange: { lower, upper }        可选（网格策略传入，画上下限参考线）
 *   color: string                      标的主题色（价格线颜色）
 */
export default function CompareTradeChart({
  priceCurve = [],
  tradeRecords = [],
  maCurve = [],
  maLabel = "",
  gridRange = null,
  color = "#6f7784",
}) {
  const sample = (arr, max = 1600) => {
    if (arr.length <= max) return arr;
    const step = Math.ceil(arr.length / max);
    return arr.filter((_, i) => i % step === 0);
  };

  const data = useMemo(() => {
    const maMap = new Map((maCurve || []).map((p) => [p.time, p.ma]));
    const buyMap = new Map();
    const sellMap = new Map();
    (tradeRecords || []).forEach((t) => {
      if (t.type === "BUY") buyMap.set(t.time, t.price);
      else sellMap.set(t.time, t.price);
    });

    const merged = (priceCurve || []).map((bar) => {
      const dt = new Date(bar.time);
      const isDailyClose = dt.getHours() === 15 && dt.getMinutes() === 0;
      const fullTime = isDailyClose
        ? dt.toLocaleDateString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit" })
        : dt.toLocaleString("zh-CN", {
            year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
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
  }, [priceCurve, tradeRecords, maCurve]);

  return (
    <ResponsiveContainer width="100%" height={360}>
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
          tickFormatter={(v) => (typeof v === "number" ? v.toFixed(3) : v)}
        />
        <Tooltip
          content={({ active, payload }) => {
            if (active && payload && payload.length) {
              const d = payload[0].payload;
              return (
                <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg text-sm">
                  <p className="font-semibold text-gray-900 mb-1">{d.fullTime}</p>
                  <p className="text-gray-700">价格: <span className="font-medium">{d.close?.toFixed(3)}</span></p>
                  {d.ma != null && (
                    <p className="text-amber-600">{maLabel}: <span className="font-medium">{d.ma.toFixed(3)}</span></p>
                  )}
                  {d.buyPrice && <p className="text-up-600 font-medium">↑ 买入: {d.buyPrice.toFixed(3)}</p>}
                  {d.sellPrice && <p className="text-down-600 font-medium">↓ 卖出: {d.sellPrice.toFixed(3)}</p>}
                </div>
              );
            }
            return null;
          }}
        />
        <Legend />

        {gridRange && typeof gridRange.upper === "number" && (
          <ReferenceLine
            y={gridRange.upper}
            stroke="#ef4444"
            strokeDasharray="5 5"
            label={{ value: "上限", position: "insideTopRight", fill: "#ef4444", fontSize: 11 }}
          />
        )}
        {gridRange && typeof gridRange.lower === "number" && (
          <ReferenceLine
            y={gridRange.lower}
            stroke="#10b981"
            strokeDasharray="5 5"
            label={{ value: "下限", position: "insideBottomRight", fill: "#10b981", fontSize: 11 }}
          />
        )}

        <Line type="monotone" dataKey="close" stroke={color} strokeWidth={2} dot={false} name="价格" />
        {maCurve && maCurve.length > 0 && (
          <Line type="monotone" dataKey="ma" stroke="#f59e0b" strokeWidth={2} dot={false} name={maLabel || "均线"} connectNulls />
        )}
        <Scatter dataKey="buyPrice" fill="#ef4444" shape="circle" name="买入" />
        <Scatter dataKey="sellPrice" fill="#3b82f6" shape="circle" name="卖出" />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

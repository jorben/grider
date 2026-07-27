import React, { useMemo, useState } from "react";
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

/**
 * 多标的收益对比图（累计收益率净值曲线，支持 1-5 个标的）。
 *
 * 显示策略：
 *  - 恰好 2 个标的：默认双 Y 轴（左=标的A策略+持有，右=标的B策略+持有），适合收益量级差距大时分别读数；
 *    可切换单轴归一化。
 *  - ≥3 个标的：单轴归一化（所有线共用一个百分比轴），每标的一条策略实线；
 *    "持有不动"虚线默认隐藏（可开关打开），避免线条过多。
 *
 * props:
 *   series: [{ code, name, color, points: [{ time, strat, hold }] }]
 *     strat / hold 为累计收益率（小数，0.12 表示 +12%）
 */
export default function CompareReturnChart({ series = [] }) {
  const list = (series || []).filter(Boolean);
  const canDual = list.length === 2;
  const [dualAxis, setDualAxis] = useState(true); // 仅 2 标的时有效
  const [showHold, setShowHold] = useState(list.length <= 2); // 多标的默认隐藏持有线

  const useDual = canDual && dualAxis;

  const data = useMemo(() => {
    const map = new Map();
    list.forEach((s, i) => {
      (s.points || []).forEach((p) => {
        const row = map.get(p.time) || { time: p.time };
        row[`s${i}_strat`] = p.strat;
        row[`s${i}_hold`] = p.hold;
        map.set(p.time, row);
      });
    });
    const rows = Array.from(map.values()).sort(
      (x, y) => new Date(x.time) - new Date(y.time)
    );
    const max = 1200;
    if (rows.length <= max) return rows;
    const step = Math.ceil(rows.length / max);
    return rows.filter((_, i) => i % step === 0);
  }, [list]);

  const fmtPct = (v) => (typeof v === "number" ? `${(v * 100).toFixed(1)}%` : "");

  return (
    <div>
      <div className="flex items-center justify-end gap-2 mb-2">
        <button
          onClick={() => setShowHold((v) => !v)}
          className="text-xs px-3 py-1 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50"
        >
          {showHold ? "隐藏持有线" : "显示持有线"}
        </button>
        {canDual && (
          <button
            onClick={() => setDualAxis((v) => !v)}
            className="text-xs px-3 py-1 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50"
          >
            {dualAxis ? "切换：单轴归一化" : "切换：双Y轴（左A右B）"}
          </button>
        )}
      </div>
      <ResponsiveContainer width="100%" height={460}>
        <ComposedChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 12 }}
            interval="preserveStartEnd"
            tickFormatter={(v) => (typeof v === "string" ? v.slice(0, 7) : v)}
          />
          <YAxis yAxisId="left" tick={{ fontSize: 12 }} tickFormatter={fmtPct} width={56} />
          {useDual && (
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: 12 }}
              tickFormatter={fmtPct}
              width={56}
            />
          )}
          <Tooltip
            content={({ active, payload, label }) => {
              if (!active || !payload || !payload.length) return null;
              return (
                <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg text-sm">
                  <p className="font-semibold text-gray-900 mb-1">{label}</p>
                  {payload.map((p) => (
                    <p key={p.dataKey} style={{ color: p.color }}>
                      {p.name}: {fmtPct(p.value)}
                    </p>
                  ))}
                </div>
              );
            }}
          />
          <Legend />

          {list.map((s, i) => {
            // 双轴模式：第0个走左轴，第1个走右轴；单轴模式：全部左轴
            const axisId = useDual ? (i === 0 ? "left" : "right") : "left";
            return (
              <Line
                key={`strat-${i}`}
                yAxisId={axisId}
                type="monotone"
                dataKey={`s${i}_strat`}
                stroke={s.color}
                strokeWidth={2}
                dot={false}
                connectNulls
                name={`${s.name} 策略`}
              />
            );
          })}

          {showHold &&
            list.map((s, i) => {
              const axisId = useDual ? (i === 0 ? "left" : "right") : "left";
              return (
                <Line
                  key={`hold-${i}`}
                  yAxisId={axisId}
                  type="monotone"
                  dataKey={`s${i}_hold`}
                  stroke={s.color}
                  strokeWidth={1.5}
                  strokeDasharray="5 4"
                  dot={false}
                  connectNulls
                  name={`${s.name} 持有`}
                />
              );
            })}
        </ComposedChart>
      </ResponsiveContainer>
      <p className="text-xs text-gray-500 mt-2">
        实线=策略累计收益，虚线=持有不动累计收益。
        {useDual
          ? "当前为双 Y 轴：左轴对应标的A、右轴对应标的B，适合两者收益量级差距大时分别读数。"
          : "当前为单轴归一化：所有线共用一个百分比轴，直接比较谁的累计收益更高。"}
      </p>
    </div>
  );
}

import React from "react";

/**
 * 多标的指标对比表。每个指标列中“最优”单元格高亮加粗。
 *
 * props:
 *   items: [{ code, name, color, metrics: { total_return, excess_return, annualized_return,
 *             max_drawdown, sharpe_ratio, win_rate, trades } }]
 */
const pct = (v) => (typeof v === "number" ? (v * 100).toFixed(2) + "%" : "N/A");
const num = (v) => (typeof v === "number" ? v.toFixed(2) : "N/A");

// 指标定义：key、标题、格式化、方向(better: 'high'越大越好 / 'low'越小越好 / null不比较)
const COLUMNS = [
  { key: "total_return", title: "策略收益", fmt: pct, better: "high", signed: true },
  { key: "excess_return", title: "超额收益", fmt: pct, better: "high", signed: true },
  { key: "annualized_return", title: "年化收益", fmt: pct, better: "high", signed: true },
  { key: "hold_return", title: "持有收益", fmt: pct, better: null, signed: true },
  { key: "max_drawdown", title: "最大回撤", fmt: pct, better: "low", signed: true },
  { key: "sharpe_ratio", title: "夏普", fmt: num, better: "high" },
  { key: "win_rate", title: "胜率", fmt: pct, better: "high" },
  { key: "trades", title: "交易次数", fmt: (v) => (v ?? "N/A"), better: null },
];

export default function CompareMetricsTable({ items = [] }) {
  // 计算每列最优 index
  const bestIndex = {};
  COLUMNS.forEach((col) => {
    if (!col.better) return;
    let best = null;
    let bestVal = null;
    items.forEach((it, i) => {
      const v = it.metrics?.[col.key];
      if (typeof v !== "number") return;
      if (
        bestVal === null ||
        (col.better === "high" && v > bestVal) ||
        (col.better === "low" && Math.abs(v) < Math.abs(bestVal))
      ) {
        bestVal = v;
        best = i;
      }
    });
    bestIndex[col.key] = best;
  });

  const signedColor = (v) =>
    typeof v === "number"
      ? v > 0
        ? "text-up-600"
        : v < 0
          ? "text-down-600"
          : "text-gray-900"
      : "text-gray-900";

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-gray-500 text-left">
            <th className="py-2 px-3">指标</th>
            {items.map((it, i) => (
              <th key={i} className="py-2 px-3 text-right">
                <span
                  className="inline-block w-2.5 h-2.5 rounded-full mr-1.5 align-middle"
                  style={{ background: it.color }}
                />
                {it.name}（{it.code}）
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {COLUMNS.map((col) => (
            <tr key={col.key} className="border-b border-gray-100">
              <td className="py-2 px-3 text-gray-600">{col.title}</td>
              {items.map((it, i) => {
                const v = it.metrics?.[col.key];
                const isBest = bestIndex[col.key] === i;
                const color = col.signed ? signedColor(v) : "text-gray-900";
                return (
                  <td
                    key={i}
                    className={`py-2 px-3 text-right ${color} ${
                      isBest ? "font-bold bg-green-50 rounded" : ""
                    }`}
                  >
                    {col.fmt(v)}
                    {isBest && <span className="ml-1 text-green-600">★</span>}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-xs text-gray-500 mt-2">★ 表示该指标在对比标的中表现最优（回撤取绝对值最小）。</p>
    </div>
  );
}

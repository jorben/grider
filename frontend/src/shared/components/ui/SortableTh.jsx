import React from "react";
import { ChevronUp, ChevronDown, ChevronsUpDown } from "lucide-react";

/**
 * 可排序表头单元格
 *
 * Props:
 * - label: 列名
 * - sortKey: 该列对应的数据字段
 * - activeKey / dir: 当前排序字段与方向
 * - onSort(sortKey): 点击回调
 * - align: 'left' | 'right'（默认 right，适合数值列）
 */
export default function SortableTh({ label, sortKey, activeKey, dir, onSort, align = "right" }) {
  const active = activeKey === sortKey;
  const justify = align === "right" ? "justify-end" : "justify-start";
  return (
    <th className={`py-3 px-2 ${align === "right" ? "text-right" : "text-left"}`}>
      <button
        type="button"
        onClick={() => onSort(sortKey)}
        className={`inline-flex items-center gap-1 ${justify} hover:text-gray-900 transition-colors ${
          active ? "text-gray-900 font-medium" : "text-gray-500"
        }`}
        title="点击排序"
      >
        <span>{label}</span>
        {active ? (
          dir === "asc" ? (
            <ChevronUp className="w-3.5 h-3.5" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5" />
          )
        ) : (
          <ChevronsUpDown className="w-3.5 h-3.5 opacity-40" />
        )}
      </button>
    </th>
  );
}

import { useState, useMemo, useCallback } from "react";

/**
 * 通用列表排序 Hook
 *
 * 用法：
 *   const { sorted, sortKey, sortDir, requestSort } = useSortableData(items, {
 *     key: "excess_return", dir: "desc",
 *   });
 *
 * - 点击同一列：在 desc -> asc 间切换
 * - 点击新列：默认 desc（数值类降序更符合"挑最好"的直觉）
 * - null/undefined 始终排在最后（无论升降序）
 * - 字符串按本地化比较（中文也可），数值按大小比较
 */
export function useSortableData(items = [], initial = { key: null, dir: "desc" }) {
  const [sortKey, setSortKey] = useState(initial.key);
  const [sortDir, setSortDir] = useState(initial.dir || "desc");

  const requestSort = useCallback(
    (key) => {
      if (key === sortKey) {
        setSortDir((d) => (d === "desc" ? "asc" : "desc"));
      } else {
        setSortKey(key);
        setSortDir("desc");
      }
    },
    [sortKey]
  );

  const sorted = useMemo(() => {
    if (!sortKey) return items;
    const arr = [...items];
    arr.sort((a, b) => {
      const va = a[sortKey];
      const vb = b[sortKey];
      const aNull = va === null || va === undefined;
      const bNull = vb === null || vb === undefined;
      if (aNull && bNull) return 0;
      if (aNull) return 1; // null 始终在后
      if (bNull) return -1;

      let cmp;
      if (typeof va === "number" && typeof vb === "number") {
        cmp = va - vb;
      } else {
        cmp = String(va).localeCompare(String(vb), "zh-Hans-CN");
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
    return arr;
  }, [items, sortKey, sortDir]);

  return { sorted, sortKey, sortDir, requestSort };
}

import React, { useState, useEffect } from "react";
import { Plus, X } from "lucide-react";
import { usePersistedState } from "@shared/hooks";
import { getBatchNames } from "@shared/services/api";

/**
 * 自定义标的代码列表
 * - 用户可添加常用代码（保存在 localStorage，跨页面/刷新共享）
 * - 点击代码即填入输入框（通过 onSelect 回调）
 * - 每个代码可删除
 * - 自动批量解析并显示标的名称（如 510300 沪深300ETF）
 *
 * 通过共享的 storageKey 让首页(网格)与均线回测页使用同一份自定义列表。
 */
const STORAGE_KEY = "customCodeList";
// 初始默认列表（用户可自行增删）
const DEFAULT_CODES = ["510300", "159915", "588000", "512170"];

// 模块级名称缓存：跨组件实例 / 跨页面复用，避免重复请求
const _nameCache = {};

export default function CustomCodeList({ value, onSelect, label = "自定义标的" }) {
  const [codes, setCodes] = usePersistedState(STORAGE_KEY, DEFAULT_CODES);
  const [adding, setAdding] = useState(false);
  const [draft, setDraft] = useState("");
  const [names, setNames] = useState(_nameCache);

  // 批量解析名称（仅对尚未缓存的代码发起请求）
  useEffect(() => {
    const missing = codes.filter((c) => !(c in _nameCache));
    if (missing.length === 0) {
      setNames({ ..._nameCache });
      return;
    }
    let cancelled = false;
    getBatchNames(missing)
      .then((resp) => {
        if (cancelled || !resp?.data) return;
        Object.assign(_nameCache, resp.data);
        setNames({ ..._nameCache });
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [codes]);

  const normalize = (c) => c.replace(/[^0-9a-zA-Z]/g, "").toUpperCase().slice(0, 6);

  const handleAdd = () => {
    const code = normalize(draft);
    if (!code) {
      setAdding(false);
      setDraft("");
      return;
    }
    if (!codes.includes(code)) {
      setCodes([...codes, code]);
    }
    setDraft("");
    setAdding(false);
    // 添加后直接填入输入框
    if (typeof onSelect === "function") onSelect(code);
  };

  const handleRemove = (code) => {
    setCodes(codes.filter((c) => c !== code));
  };

  return (
    <div className="flex items-center flex-wrap gap-2">
      <span className="hidden sm:inline text-xs text-gray-500 mr-1">{label}</span>
      <div className="flex flex-wrap items-center gap-2">
        {codes.map((code) => {
          const nm = names[code] && names[code] !== code ? names[code] : "";
          return (
            <span
              key={code}
              className={`group inline-flex items-center gap-1 px-3 py-1 text-xs rounded-full border transition-colors cursor-pointer ${
                value === code
                  ? "bg-blue-100 border-blue-300 text-blue-700"
                  : "bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100"
              }`}
              onClick={() => onSelect && onSelect(code)}
              title={nm ? `${code} ${nm}` : code}
            >
              <span className="font-medium">{code}</span>
              {nm && <span className="text-gray-400">{nm}</span>}
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemove(code);
                }}
                className="text-gray-400 hover:text-red-500"
                title="删除"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          );
        })}

        {adding ? (
          <span className="inline-flex items-center gap-1">
            <input
              autoFocus
              value={draft}
              onChange={(e) => setDraft(normalize(e.target.value))}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleAdd();
                if (e.key === "Escape") {
                  setAdding(false);
                  setDraft("");
                }
              }}
              onBlur={handleAdd}
              placeholder="代码"
              className="w-20 px-2 py-1 text-xs border border-gray-300 rounded-full focus:ring-1 focus:ring-blue-400"
            />
          </span>
        ) : (
          <button
            type="button"
            onClick={() => setAdding(true)}
            className="inline-flex items-center gap-1 px-3 py-1 text-xs rounded-full border border-dashed border-gray-300 text-gray-500 hover:bg-gray-50 hover:text-blue-600"
          >
            <Plus className="w-3 h-3" />
            添加
          </button>
        )}
      </div>
    </div>
  );
}

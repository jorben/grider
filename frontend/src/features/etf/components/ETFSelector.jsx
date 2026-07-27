import React from "react";
import { Search, TrendingUp } from "lucide-react";
import ETFInfoSkeleton from "./ETFInfoSkeleton";
import CustomCodeList from "./CustomCodeList";

/**
 * ETF选择器组件
 * 负责ETF代码输入、自定义标的选择、ETF信息展示
 */
export default function ETFSelector({
  value,
  onChange,
  error,
  popularETFs = [],
  etfInfo,
  loading,
}) {
  return (
    <div>
      <div className="mb-3">
        <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
          <Search className="w-4 h-4" />
          标的选择
        </label>

        {/* 自定义标的（可增删、点击填入），独占一行以容纳更多代码 */}
        <CustomCodeList value={value} onSelect={onChange} />
      </div>

      <div className="relative">
        <input
          type="text"
          value={value}
          onChange={(e) =>
            onChange(e.target.value.replace(/[^0-9a-zA-Z]/g, "").toUpperCase())
          }
          placeholder="请输入标的代码，如：510300、603137、SPY；场外基金加F，如 F007339"
          className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
            error ? "border-red-300" : "border-gray-300"
          }`}
          maxLength={7}
        />
        <p className="mt-1 text-xs text-gray-400">
          场外（开放式）基金请在代码开头或结尾加字母 F，例如 F007339，以便与场内个股/ETF 区分。
        </p>

        {/* 标的信息区域 */}
        <div className="mt-2" style={{ minHeight: "80px" }}>
          {loading && <ETFInfoSkeleton />}

          {!loading && etfInfo &&
            (etfInfo.code === value ||
              value.replace(/^[FO]|[FO]$/g, "") === etfInfo.code) && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-blue-600" />
                <span className="font-medium text-blue-800">
                  {etfInfo.name}
                </span>
                <span className="text-sm text-blue-600">
                  {etfInfo.country === 'CHN' ? '¥' : etfInfo.country === 'USA' ? '$' : etfInfo.country === 'HKG' ? 'HK$' : '¥'}{etfInfo.current_price?.toFixed(3)}
                  <span
                    className={
                      etfInfo.change_pct >= 0
                        ? "text-up-600"  /* 红色 - 上涨 */
                        : "text-down-600"  /* 绿色 - 下跌 */
                    }
                  >
                    ({etfInfo.change_pct >= 0 ? "+" : ""}
                    {etfInfo.change_pct?.toFixed(2)}%)
                  </span>
                </span>
              </div>
              <p className="text-xs text-blue-600 mt-1">
                数据时间：{etfInfo.date}
              </p>
            </div>
          )}

          {!loading && error && (
            <p className="mt-1 text-sm text-red-600">{error}</p>
          )}
        </div>
      </div>
    </div>
  );
}

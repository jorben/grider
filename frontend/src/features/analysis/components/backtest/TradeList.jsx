import React, { useState, useMemo } from 'react';
import { formatCurrency } from '@shared/utils/format';

/**
 * 交易记录列表
 */
export default function TradeList({ trades = [] }) {
  const [filter, setFilter] = useState('ALL'); // 'ALL' | 'BUY' | 'SELL'

  const filteredTrades = useMemo(() => {
    if (filter === 'ALL') return trades;
    return trades.filter((t) => t.type === filter);
  }, [trades, filter]);

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">交易记录</h3>

        {/* 筛选器 */}
        <div className="flex space-x-2">
          {['ALL', 'BUY', 'SELL'].map((type) => (
            <button
              key={type}
              onClick={() => setFilter(type)}
              className={`px-3 py-1 rounded text-sm ${
                filter === type
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {type === 'ALL' ? '全部' : type === 'BUY' ? '买入' : '卖出'}
            </button>
          ))}
        </div>
      </div>

      {/* 交易表格 */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                时间
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                类型
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                价格
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                数量
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                手续费
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                盈亏
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                持仓
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                资金余额
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredTrades.map((trade, index) => (
              <tr
                key={index}
                className={
                  trade.type === 'BUY'
                    ? 'bg-red-50 hover:bg-red-100'
                    : 'bg-blue-50 hover:bg-blue-100'
                }
              >
                <td className="px-4 py-3 text-sm text-gray-900">
                  {new Date(trade.time).toLocaleString('zh-CN', {
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </td>
                <td className="px-4 py-3 text-sm">
                  <span
                    className={`px-2 py-1 rounded text-xs font-semibold ${
                      trade.type === 'BUY'
                        ? 'bg-red-200 text-red-800'
                        : 'bg-blue-200 text-blue-800'
                    }`}
                  >
                    {trade.type === 'BUY' ? '买入' : '卖出'}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">
                  {trade.price.toFixed(3)}
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">
                  {trade.quantity}股
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-600">
                  {formatCurrency(trade.commission)}
                </td>
                <td className="px-4 py-3 text-sm text-right">
                  {trade.profit !== null ? (
                    <span
                      className={
                        trade.profit > 0
                          ? 'text-red-600 font-semibold'
                          : trade.profit < 0
                          ? 'text-green-600'
                          : 'text-gray-600'
                      }
                    >
                      {trade.profit > 0 ? '+' : ''}
                      {formatCurrency(trade.profit)}
                    </span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">
                  {trade.position}股
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">
                  {formatCurrency(trade.cash)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredTrades.length === 0 && (
        <div className="text-center py-8 text-gray-500">暂无交易记录</div>
      )}
    </div>
  );
}
import React, { useState, useMemo } from 'react';
import { formatCurrency } from '@shared/utils/format';
import { TrendingUp, TrendingDown, Filter, Calendar, DollarSign, Hash, Percent, Activity } from 'lucide-react';

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
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-r from-green-100 to-blue-100 rounded-lg">
            <Activity className="w-5 h-5 text-gradient-to-r from-green-600 to-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">交易记录</h3>
            <p className="text-sm text-gray-600">网格策略执行详情</p>
          </div>
        </div>

        {/* 筛选器 */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <div className="flex space-x-1">
            {['ALL', 'BUY', 'SELL'].map((type) => (
              <button
                key={type}
                onClick={() => setFilter(type)}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  filter === type
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {type === 'ALL' ? '全部' : type === 'BUY' ? '买入' : '卖出'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 交易表格 */}
      <div className="overflow-x-auto">
        <table className="responsive-table">
          <thead>
            <tr>
              <th className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                时间
              </th>
              <th>类型</th>
              <th className="text-right">
                <DollarSign className="w-3 h-3 inline mr-1" />
                价格
              </th>
              <th className="text-right">
                <Hash className="w-3 h-3 inline mr-1" />
                数量
              </th>
              <th className="text-right">
                <Percent className="w-3 h-3 inline mr-1" />
                手续费
              </th>
              <th className="text-right">盈亏</th>
              <th className="text-right">持仓</th>
              <th className="text-right">资金余额</th>
            </tr>
          </thead>
          <tbody>
            {filteredTrades.map((trade, index) => (
              <tr
                key={index}
                className={`transition-colors ${
                  trade.type === 'BUY'
                    ? 'hover:bg-red-50'
                    : 'hover:bg-blue-50'
                }`}
              >
                <td className="text-sm text-gray-900">
                  {new Date(trade.time).toLocaleString('zh-CN', {
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </td>
                <td>
                  <span
                    className={`badge ${
                      trade.type === 'BUY' ? 'badge-danger' : 'badge-info'
                    }`}
                  >
                    {trade.type === 'BUY' ? (
                      <TrendingUp className="w-3 h-3 mr-1" />
                    ) : (
                      <TrendingDown className="w-3 h-3 mr-1" />
                    )}
                    {trade.type === 'BUY' ? '买入' : '卖出'}
                  </span>
                </td>
                <td className="text-sm text-right text-gray-900 font-medium">
                  {trade.price.toFixed(3)}
                </td>
                <td className="text-sm text-right text-gray-900">
                  {trade.quantity}股
                </td>
                <td className="text-sm text-right text-gray-600">
                  {formatCurrency(trade.commission)}
                </td>
                <td className="text-sm text-right">
                  {trade.profit !== null ? (
                    <span
                      className={`font-medium ${
                        trade.profit > 0
                          ? 'text-red-600'
                          : trade.profit < 0
                          ? 'text-green-600'
                          : 'text-gray-600'
                      }`}
                    >
                      {trade.profit > 0 ? '+' : ''}
                      {formatCurrency(trade.profit)}
                    </span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="text-sm text-right text-gray-900">
                  {trade.position}股
                </td>
                <td className="text-sm text-right text-gray-900 font-medium">
                  {formatCurrency(trade.cash)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredTrades.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <Activity className="w-8 h-8 mx-auto mb-2 text-gray-400" />
          <p>暂无交易记录</p>
        </div>
      )}
    </div>
  );
}
import React, { useState, useMemo } from 'react';
import { formatCurrency } from '@shared/utils/format';
import { TrendingUp, TrendingDown, Filter, Calendar, DollarSign, Hash, Percent, Activity, ChevronLeft, ChevronRight, BarChart3, Download } from 'lucide-react';
import * as XLSX from 'xlsx';

/**
 * 交易记录列表
 */
export default function TradeList({ trades = [], gridStrategy, totalCapital }) {
  const [filter, setFilter] = useState('ALL'); // 'ALL' | 'BUY' | 'SELL'
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  // 计算增强的交易记录（包含市值、总资产、总盈亏额）
  const enhancedTrades = useMemo(() => {
    if (!gridStrategy || !totalCapital) return trades;

    const reserveAmount = gridStrategy.fund_allocation?.reserve_amount || 0;

    return trades.map((trade, index) => {
      const marketValue = trade.price * trade.position; // 市值 = 交易价格 × 持仓
      const totalAsset = marketValue + trade.cash + reserveAmount; // 总资产 = 市值 + 资金余额 + 预留资金
      const totalProfitLoss = totalAsset - totalCapital; // 总盈亏额 = 总资产 - 初始资产

      return {
        ...trade,
        marketValue: Math.round(marketValue * 100) / 100,
        totalAsset: Math.round(totalAsset * 100) / 100,
        totalProfitLoss: Math.round(totalProfitLoss * 100) / 100,
        isFirstTrade: index === 0,
      };
    });
  }, [trades, gridStrategy, totalCapital]);

  const filteredTrades = useMemo(() => {
    if (filter === 'ALL') return enhancedTrades;
    return enhancedTrades.filter((t) => t.type === filter);
  }, [enhancedTrades, filter]);

  // 分页计算
  const totalPages = Math.ceil(filteredTrades.length / pageSize);
  const currentPageData = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return filteredTrades.slice(startIndex, endIndex);
  }, [filteredTrades, currentPage, pageSize]);

  // 重置页码当筛选条件改变时
  const handleFilterChange = (newFilter) => {
    setFilter(newFilter);
    setCurrentPage(1);
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handleExportExcel = () => {
    try {
      // 准备导出数据
      const exportData = filteredTrades.map((trade, index) => ({
        '序号': index + 1,
        '时间': new Date(trade.time).toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        }),
        '类型': trade.type === 'BUY' ? (trade.isFirstTrade ? '建仓' : '买入') : '卖出',
        '价格': trade.price.toFixed(3),
        '数量': trade.quantity,
        '手续费': trade.commission.toFixed(3),
        '持仓': trade.position,
        '网格余额': trade.cash,
        '持仓市值': trade.marketValue !== undefined ? trade.marketValue : '',
        '总资产': trade.totalAsset !== undefined ? trade.totalAsset : '',
        '总盈亏': trade.totalProfitLoss !== undefined ? trade.totalProfitLoss : ''
      }));

      // 创建工作簿
      const wb = XLSX.utils.book_new();

      // 创建工作表
      const ws = XLSX.utils.json_to_sheet(exportData, {
        header: [
          '序号',
          '时间',
          '类型',
          '价格',
          '数量',
          '手续费',
          '持仓',
          '网格余额',
          '持仓市值',
          '总资产',
          '总盈亏'
        ]
      });

      // 设置列宽
      const colWidths = [
        { wch: 8 },  // 序号
        { wch: 20 }, // 时间
        { wch: 8 },  // 类型
        { wch: 12 }, // 价格
        { wch: 12 }, // 数量
        { wch: 12 }, // 手续费
        { wch: 12 }, // 持仓
        { wch: 15 }, // 网格余额
        { wch: 15 }, // 持仓市值
        { wch: 15 }, // 总资产
        { wch: 15 }  // 总盈亏
      ];
      ws['!cols'] = colWidths;

      // 添加工作表到工作簿
      XLSX.utils.book_append_sheet(wb, ws, '交易记录');

      // 生成文件名（包含当前时间）
      const now = new Date();
      const timestamp = now.toISOString().slice(0, 19).replace(/[:]/g, '-');
      const filename = `交易记录_${timestamp}.xlsx`;

      // 导出Excel文件
      XLSX.writeFile(wb, filename);

    } catch (error) {
      console.error('导出Excel失败:', error);
      alert('导出Excel失败，请稍后重试');
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 hidden md:block">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-r from-green-100 to-blue-100 rounded-lg">
            <Activity className="w-5 h-5 text-gradient-to-r from-green-600 to-blue-600" />
          </div>
          <div>
            <h4 className="font-semibold text-gray-900">交易记录</h4>
            <p className="text-sm text-gray-600">网格策略执行详情</p>
          </div>
        </div>

        {/* 筛选器和导出按钮 */}
        <div className="flex items-center gap-3">
          {/* 筛选器 */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <div className="flex space-x-1">
              {['ALL', 'BUY', 'SELL'].map((type) => (
                <button
                  key={type}
                  onClick={() => handleFilterChange(type)}
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

          {/* 导出按钮 */}
          <button
            onClick={handleExportExcel}
            disabled={filteredTrades.length === 0}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
            title="导出Excel文件"
          >
            <Download className="w-4 h-4" />
            导出
          </button>
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
              {/*<th className="text-right">盈亏</th>*/}
              <th className="text-right">持仓</th>
              <th className="text-right">网格余额</th>
              <th className="text-right">
                <BarChart3 className="w-3 h-3 inline mr-1" />
                持仓市值
              </th>
              <th className="text-right">
                <DollarSign className="w-3 h-3 inline mr-1" />
                总资产
              </th>
              <th className="text-right">
                <TrendingUp className="w-3 h-3 inline mr-1" />
                总盈亏
              </th>
            </tr>
          </thead>
          <tbody>
            {currentPageData.map((trade, index) => (
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
                    {trade.type === 'BUY' ? (trade.isFirstTrade ? '建仓' : '买入') : '卖出'}
                  </span>
                </td>
                <td className="text-sm text-right text-gray-900 font-medium">
                  {trade.price.toFixed(3)}
                </td>
                <td className="text-sm text-right text-gray-900">
                  {trade.quantity}股
                </td>
                <td className="text-sm text-right text-gray-600">
                  {formatCurrency(trade.commission, 'CHN', { maximumFractionDigits: 3 })}
                </td>
                {/*<td className="text-sm text-right">
                  {trade.profit !== null ? (
                    <span
                      className="font-medium"
                    >
                      {trade.profit > 0 ? '+' : ''}
                      {formatCurrency(trade.profit)}
                    </span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>*/}
                <td className="text-sm text-right text-gray-900">
                  {trade.position}股
                </td>
                <td className="text-sm text-right text-gray-900 font-medium">
                  {formatCurrency(trade.cash)}
                </td>
                <td className="text-sm text-right text-gray-900">
                  {trade.marketValue !== undefined ? formatCurrency(trade.marketValue) : '-'}
                </td>
                <td className="text-sm text-right text-gray-900 font-medium">
                  {trade.totalAsset !== undefined ? formatCurrency(trade.totalAsset) : '-'}
                </td>
                <td className="text-sm text-right">
                  {trade.totalProfitLoss !== undefined ? (
                    <span
                      className={`font-medium ${
                        trade.totalProfitLoss > 0
                          ? 'text-up-600'  /* 红色 - 盈利 */
                          : trade.totalProfitLoss < 0
                            ? 'text-down-600'  /* 绿色 - 亏损 */
                            : 'text-gray-600'
                      }`}
                    >
                      {trade.totalProfitLoss > 0 ? '+' : ''}
                      {formatCurrency(trade.totalProfitLoss)}
                    </span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 分页控件 */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4 px-4">
          <div className="text-sm text-gray-600">
            显示第 {(currentPage - 1) * pageSize + 1} - {Math.min(currentPage * pageSize, filteredTrades.length)} 条，共 {filteredTrades.length} 条记录
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="flex items-center gap-1 px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
              上一页
            </button>
            <span className="text-sm text-gray-600">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="flex items-center gap-1 px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一页
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {filteredTrades.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <Activity className="w-8 h-8 mx-auto mb-2 text-gray-400" />
          <p>暂无交易记录</p>
        </div>
      )}
    </div>
  );
}
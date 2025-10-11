import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { formatCurrency } from '@shared/utils/format';

/**
 * 网格表现分析组件
 */
export default function GridPerformance({ gridAnalysis = null, priceLevels = [] }) {
  // 准备网格数据
  const gridData = useMemo(() => {
    if (!gridAnalysis || !gridAnalysis.grid_performance) return [];

    return gridAnalysis.grid_performance.map((grid) => ({
      price: grid.price.toFixed(3),
      triggerCount: grid.trigger_count,
      profitContribution: grid.profit_contribution,
      triggered: grid.trigger_count > 0,
    }));
  }, [gridAnalysis]);

  // 颜色映射
  const getBarColor = (triggerCount) => {
    if (triggerCount === 0) return '#e5e7eb'; // 灰色 - 未触发
    if (triggerCount <= 2) return '#93c5fd'; // 浅蓝 - 低频
    if (triggerCount <= 5) return '#3b82f6'; // 蓝色 - 中频
    return '#1e40af'; // 深蓝 - 高频
  };

  if (!gridAnalysis) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <p className="text-gray-500 text-center py-8">暂无网格分析数据</p>
      </div>
    );
  }

  const { triggered_grids, total_grids } = gridAnalysis;
  const triggerRate = (triggered_grids / total_grids * 100).toFixed(1);

  return (
    <div className="space-y-4">
      {/* 网格概览 */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-4">网格表现分析</h3>

        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center p-3 bg-blue-50 rounded">
            <p className="text-sm text-gray-600 mb-1">总网格数</p>
            <p className="text-2xl font-bold text-blue-600">{total_grids}</p>
          </div>
          <div className="text-center p-3 bg-green-50 rounded">
            <p className="text-sm text-gray-600 mb-1">已触发</p>
            <p className="text-2xl font-bold text-green-600">{triggered_grids}</p>
          </div>
          <div className="text-center p-3 bg-purple-50 rounded">
            <p className="text-sm text-gray-600 mb-1">触发率</p>
            <p className="text-2xl font-bold text-purple-600">{triggerRate}%</p>
          </div>
        </div>

        {/* 触发频率图例 */}
        <div className="flex justify-center space-x-4 mb-4 text-sm">
          <div className="flex items-center">
            <div className="w-4 h-4 bg-gray-200 rounded mr-2"></div>
            <span className="text-gray-600">未触发</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-blue-300 rounded mr-2"></div>
            <span className="text-gray-600">低频(1-2次)</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-blue-500 rounded mr-2"></div>
            <span className="text-gray-600">中频(3-5次)</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-blue-700 rounded mr-2"></div>
            <span className="text-gray-600">高频(6次+)</span>
          </div>
        </div>

        {/* 网格触发频率图 */}
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={gridData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="price"
              tick={{ fontSize: 11 }}
              interval="preserveStartEnd"
              label={{ value: '网格价格', position: 'insideBottom', offset: -5 }}
            />
            <YAxis
              tick={{ fontSize: 11 }}
              label={{ value: '触发次数', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white p-3 border border-gray-300 rounded shadow">
                      <p className="text-sm font-semibold">价格: {data.price}</p>
                      <p className="text-sm">触发次数: {data.triggerCount}</p>
                      <p className="text-sm text-green-600">
                        盈利贡献: {formatCurrency(data.profitContribution)}
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="triggerCount" name="触发次数">
              {gridData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.triggerCount)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* 网格详细表格 */}
      <div className="bg-white rounded-lg shadow p-4">
        <h4 className="text-md font-semibold mb-3">网格明细</h4>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  网格价格
                </th>
                <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">
                  触发次数
                </th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                  盈利贡献
                </th>
                <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">
                  状态
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {gridData.slice(0, 10).map((grid, index) => (
                <tr key={index} className={grid.triggered ? 'bg-blue-50' : ''}>
                  <td className="px-4 py-2 text-sm text-gray-900">{grid.price}</td>
                  <td className="px-4 py-2 text-sm text-center text-gray-900">
                    {grid.triggerCount}次
                  </td>
                  <td className="px-4 py-2 text-sm text-right">
                    <span className={grid.profitContribution > 0 ? 'text-green-600' : 'text-gray-600'}>
                      {formatCurrency(grid.profitContribution)}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-sm text-center">
                    <span className={`px-2 py-1 rounded text-xs ${
                      grid.triggered
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {grid.triggered ? '已触发' : '未触发'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {gridData.length > 10 && (
            <p className="text-sm text-gray-500 text-center mt-3">
              显示前10个网格，共{gridData.length}个
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
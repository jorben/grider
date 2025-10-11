import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { formatCurrency } from '@shared/utils/format';
import { Grid3X3, Activity, Target, CheckCircle, XCircle } from 'lucide-react';

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
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <p className="text-gray-500 text-center py-8">暂无网格分析数据</p>
      </div>
    );
  }

  const { triggered_grids, total_grids } = gridAnalysis;
  const triggerRate = (triggered_grids / total_grids * 100).toFixed(1);

  return (
    <div className="space-y-6">
      {/* 网格概览 */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-gradient-to-r from-purple-100 to-indigo-100 rounded-lg">
            <Grid3X3 className="w-5 h-5 text-gradient-to-r from-purple-600 to-indigo-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">网格表现分析</h3>
            <p className="text-sm text-gray-600">各网格点位的触发频率和盈利贡献</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-center w-10 h-10 mx-auto mb-2 bg-blue-100 rounded-full">
              <Grid3X3 className="w-5 h-5 text-blue-600" />
            </div>
            <p className="text-sm text-gray-600 mb-1">总网格数</p>
            <p className="text-xl font-bold text-blue-600">{total_grids}</p>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="flex items-center justify-center w-10 h-10 mx-auto mb-2 bg-green-100 rounded-full">
              <Activity className="w-5 h-5 text-green-600" />
            </div>
            <p className="text-sm text-gray-600 mb-1">已触发</p>
            <p className="text-xl font-bold text-green-600">{triggered_grids}</p>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="flex items-center justify-center w-10 h-10 mx-auto mb-2 bg-purple-100 rounded-full">
              <Target className="w-5 h-5 text-purple-600" />
            </div>
            <p className="text-sm text-gray-600 mb-1">触发率</p>
            <p className="text-xl font-bold text-purple-600">{triggerRate}%</p>
          </div>
        </div>

        {/* 触发频率图例 */}
        <div className="flex justify-center space-x-6 mb-4 text-sm">
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
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
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
                    <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
                      <p className="text-sm font-semibold text-gray-900 mb-2">网格价格: {data.price}</p>
                      <div className="space-y-1 text-sm">
                        <p className="text-gray-700">触发次数: <span className="font-medium">{data.triggerCount}</span></p>
                        <p className="text-green-600 font-medium">
                          盈利贡献: {formatCurrency(data.profitContribution)}
                        </p>
                      </div>
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
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-gray-100 rounded-lg">
            <Grid3X3 className="w-5 h-5 text-gray-600" />
          </div>
          <h4 className="font-semibold text-gray-900">网格明细</h4>
        </div>
        <div className="overflow-x-auto">
          <table className="responsive-table">
            <thead>
              <tr>
                <th>网格价格</th>
                <th className="text-center">触发次数</th>
                <th className="text-right">盈利贡献</th>
                <th className="text-center">状态</th>
              </tr>
            </thead>
            <tbody>
              {gridData.slice(0, 10).map((grid, index) => (
                <tr key={index} className={grid.triggered ? 'bg-blue-50' : ''}>
                  <td className="text-sm text-gray-900 font-medium">{grid.price}</td>
                  <td className="text-sm text-center text-gray-900">
                    {grid.triggerCount}次
                  </td>
                  <td className="text-sm text-right">
                    <span className={`font-medium ${
                      grid.profitContribution > 0 ? 'text-green-600' : 'text-gray-600'
                    }`}>
                      {formatCurrency(grid.profitContribution)}
                    </span>
                  </td>
                  <td className="text-sm text-center">
                    <span className={`status-indicator ${
                      grid.triggered ? 'status-success' : 'status-warning'
                    }`}>
                      {grid.triggered ? (
                        <CheckCircle className="w-3 h-3 mr-1" />
                      ) : (
                        <XCircle className="w-3 h-3 mr-1" />
                      )}
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
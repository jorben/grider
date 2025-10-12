import React, { useMemo } from 'react';
import {
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Scatter,
  ComposedChart,
} from 'recharts';
import { TrendingUp, BarChart3, DollarSign, Target, Calendar } from 'lucide-react';

/**
 * 回测图表组件
 */
export default function BacktestCharts({ priceCurve = [], equityCurve = [], tradeRecords = [], gridStrategy = {} }) {
  // 数据抽样函数
  const sampleData = (data, maxPoints = 2400) => {
    if (data.length <= maxPoints) return data;

    const step = Math.ceil(data.length / maxPoints);
    return data.filter((_, index) => index % step === 0);
  };

  // 合并价格和交易数据（带缓存优化）
  const priceData = useMemo(() => {
    const merged = priceCurve.map((bar) => {
      const buyTrades = tradeRecords.filter(
        (t) => t.type === 'BUY' && t.time === bar.time
      );
      const sellTrades = tradeRecords.filter(
        (t) => t.type === 'SELL' && t.time === bar.time
      );

      return {
        time: new Date(bar.time).toLocaleString('zh-CN', {
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
        }),
        fullTime: bar.time,
        close: bar.close,
        high: bar.high,
        low: bar.low,
        buyPrice: buyTrades.length > 0 ? buyTrades[0].price : null,
        sellPrice: sellTrades.length > 0 ? sellTrades[0].price : null,
      };
    });

    // 对大数据量进行抽样
    return sampleData(merged);
  }, [priceCurve, tradeRecords]);

  // 准备收益曲线数据（带缓存优化）
  const equityData = useMemo(() => {
    const processed = equityCurve.map((point, index) => {
      const initialAsset = equityCurve[0].total_asset;
      const gridReturn = ((point.total_asset - initialAsset) / initialAsset) * 100;

      const pricePoint = priceCurve[index];
      const holdReturn = pricePoint
        ? ((pricePoint.close - priceCurve[0].close) / priceCurve[0].close) * 100
        : 0;

      return {
        time: new Date(point.time).toLocaleString('zh-CN', {
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
        }),
        gridReturn,
        holdReturn,
        excess: gridReturn - holdReturn,
      };
    });

    // 对大数据量进行抽样
    return sampleData(processed);
  }, [equityCurve, priceCurve]);

  const { price_range, current_price } = gridStrategy;

  return (
    <div className="space-y-6">
      {/* 主图：价格走势 + 买卖点 */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-gradient-to-r from-green-100 to-blue-100 rounded-lg">
            <TrendingUp className="w-5 h-5 text-gradient-to-r from-blue-600 to-purple-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">行情与交易</h3>
            <p className="text-sm text-gray-600">价格走势与网格交易点位</p>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={priceData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 12 }}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={['dataMin - 0.1', 'dataMax + 0.1']}
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => value.toFixed(3)}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
                      <p className="text-sm font-semibold text-gray-900 mb-2">{data.fullTime}</p>
                      <div className="space-y-1 text-sm">
                        <p className="text-gray-700">价格: <span className="font-medium">{data.close.toFixed(3)}</span></p>
                        <p className="text-gray-700">最高: <span className="font-medium">{data.high.toFixed(3)}</span></p>
                        <p className="text-gray-700">最低: <span className="font-medium">{data.low.toFixed(3)}</span></p>
                        {data.buyPrice && (
                          <p className="text-red-600 font-medium">
                            ↑ 买入: {data.buyPrice.toFixed(3)}
                          </p>
                        )}
                        {data.sellPrice && (
                          <p className="text-blue-600 font-medium">
                            ↓ 卖出: {data.sellPrice.toFixed(3)}
                          </p>
                        )}
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend />

            {/* 价格上下限参考线 */}
            <ReferenceLine
              y={price_range.upper}
              stroke="#ef4444"
              strokeDasharray="5 5"
              label={{ value: '上限', position: 'insideTopRight', fill: '#ef4444' }}
            />
            <ReferenceLine
              y={price_range.lower}
              stroke="#22c55e"
              strokeDasharray="5 5"
              label={{ value: '下限', position: 'insideBottomRight', fill: '#22c55e' }}
            />

            {/* 收盘价折线 */}
            <Line
              type="monotone"
              dataKey="close"
              stroke="#6f7784"
              strokeWidth={2}
              dot={false}
              name="价格"
            />

            {/* 买入点 */}
            <Scatter
              dataKey="buyPrice"
              fill="#ef4444"
              shape="circle"
              name="买入"
            />

            {/* 卖出点 */}
            <Scatter
              dataKey="sellPrice"
              fill="#3b82f6"
              shape="circle"
              name="卖出"
            />
          </ComposedChart>
        </ResponsiveContainer>

        {/* 副图：收益曲线对比 */}
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-gradient-to-r from-blue-100 to-purple-100 rounded-lg">
            <BarChart3 className="w-5 h-5 text-gradient-to-r from-green-600 to-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">收益对比</h3>
            <p className="text-sm text-gray-600">网格策略与持有不动策略收益对比</p>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={equityData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 12 }}
              interval="preserveStartEnd"
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
                      <p className="text-sm font-semibold text-gray-900 mb-2">{data.time}</p>
                      <div className="space-y-1 text-sm">
                        <p className="text-blue-600 font-medium">
                          网格策略: {data.gridReturn.toFixed(2)}%
                        </p>
                        <p className="text-gray-600 font-medium">
                          持有不动: {data.holdReturn.toFixed(2)}%
                        </p>
                        <p className={`font-medium ${
                          data.excess >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          超额收益: {data.excess.toFixed(2)}%
                        </p>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend />

            {/* 网格策略收益 */}
            <Area
              type="monotone"
              dataKey="gridReturn"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.3}
              name="网格策略"
            />

            {/* 持有不动收益 */}
            <Line
              type="monotone"
              dataKey="holdReturn"
              stroke="#9ca3af"
              strokeDasharray="5 5"
              dot={false}
              name="持有不动"
            />

            {/* 零线 */}
            <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="3 3" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
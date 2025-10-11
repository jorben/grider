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

/**
 * 回测图表组件
 */
export default function BacktestCharts({ priceCurve = [], equityCurve = [], tradeRecords = [], gridStrategy = {} }) {
  // 数据抽样函数
  const sampleData = (data, maxPoints = 500) => {
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
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-4">价格走势与交易点位</h3>
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={priceData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 12 }}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={['dataMin - 0.1', 'dataMax + 0.1']}
              tick={{ fontSize: 12 }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white p-3 border border-gray-300 rounded shadow">
                      <p className="text-sm font-semibold">{data.fullTime}</p>
                      <p className="text-sm">收盘价: {data.close.toFixed(3)}</p>
                      <p className="text-sm">最高: {data.high.toFixed(3)}</p>
                      <p className="text-sm">最低: {data.low.toFixed(3)}</p>
                      {data.buyPrice && (
                        <p className="text-sm text-red-600">
                          ↑ 买入: {data.buyPrice.toFixed(3)}
                        </p>
                      )}
                      {data.sellPrice && (
                        <p className="text-sm text-blue-600">
                          ↓ 卖出: {data.sellPrice.toFixed(3)}
                        </p>
                      )}
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
              stroke="red"
              strokeDasharray="5 5"
              label="上限"
            />
            <ReferenceLine
              y={price_range.lower}
              stroke="green"
              strokeDasharray="5 5"
              label="下限"
            />
            <ReferenceLine
              y={current_price}
              stroke="gray"
              strokeDasharray="3 3"
              label="基准"
            />

            {/* 收盘价折线 */}
            <Line
              type="monotone"
              dataKey="close"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              name="收盘价"
            />

            {/* 买入点 */}
            <Scatter
              dataKey="buyPrice"
              fill="red"
              shape="triangle"
              name="买入"
            />

            {/* 卖出点 */}
            <Scatter
              dataKey="sellPrice"
              fill="blue"
              shape="triangleDown"
              name="卖出"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* 副图：收益曲线对比 */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-4">收益曲线对比</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={equityData}>
            <CartesianGrid strokeDasharray="3 3" />
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
                    <div className="bg-white p-3 border border-gray-300 rounded shadow">
                      <p className="text-sm font-semibold">{data.time}</p>
                      <p className="text-sm text-blue-600">
                        网格策略: {data.gridReturn.toFixed(2)}%
                      </p>
                      <p className="text-sm text-gray-600">
                        持有不动: {data.holdReturn.toFixed(2)}%
                      </p>
                      <p className="text-sm text-green-600">
                        超额收益: {data.excess.toFixed(2)}%
                      </p>
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
            <ReferenceLine y={0} stroke="#000" strokeDasharray="3 3" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
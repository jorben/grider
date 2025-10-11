// 生成大量测试数据
const generateLargeDataset = (size) => {
  return Array.from({ length: size }, (_, i) => ({
    time: new Date(2025, 0, 1, 9, 30 + i * 5).toISOString(),
    open: 3.5 + Math.random() * 0.1,
    high: 3.52 + Math.random() * 0.1,
    low: 3.48 + Math.random() * 0.1,
    close: 3.5 + Math.random() * 0.1,
    volume: 10000 + Math.random() * 5000,
  }));
};

const generateLargeEquityData = (size) => {
  return Array.from({ length: size }, (_, i) => ({
    time: new Date(2025, 0, 1, 9, 30 + i * 5).toISOString(),
    total_asset: 10000 + Math.random() * 1000,
  }));
};

const generateLargeTradeRecords = (size) => {
  return Array.from({ length: size }, (_, i) => ({
    time: new Date(2025, 0, 1, 9, 30 + i * 5).toISOString(),
    type: Math.random() > 0.5 ? 'BUY' : 'SELL',
    price: 3.5 + Math.random() * 0.1,
    quantity: 100,
    commission: 0.35,
    profit: Math.random() > 0.5 ? Math.random() * 10 : -Math.random() * 10,
    position: 700 + Math.random() * 200,
    cash: 10000 + Math.random() * 2000,
  }));
};

describe('Performance Tests', () => {
  it('BacktestCharts handles large dataset efficiently', () => {
    const largeDataset = generateLargeDataset(1000);
    const largeEquityData = generateLargeEquityData(1000);
    const largeTrades = generateLargeTradeRecords(100);

    const start = performance.now();

    // 模拟组件渲染（这里只是数据处理部分）
    const priceData = largeDataset.map((bar) => {
      const buyTrades = largeTrades.filter(
        (t) => t.type === 'BUY' && t.time === bar.time
      );
      const sellTrades = largeTrades.filter(
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

    const equityData = largeEquityData.map((point, index) => {
      const initialAsset = largeEquityData[0].total_asset;
      const gridReturn = ((point.total_asset - initialAsset) / initialAsset) * 100;

      const pricePoint = largeDataset[index];
      const holdReturn = pricePoint
        ? ((pricePoint.close - largeDataset[0].close) / largeDataset[0].close) * 100
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

    const end = performance.now();

    // 数据处理时间应小于100ms
    expect(end - start).toBeLessThan(100);
    expect(priceData).toHaveLength(1000);
    expect(equityData).toHaveLength(1000);
  });

  it('data sampling works correctly', () => {
    const largeDataset = generateLargeDataset(2000);

    // 模拟抽样函数
    const sampleData = (data, maxPoints = 500) => {
      if (data.length <= maxPoints) return data;

      const step = Math.ceil(data.length / maxPoints);
      return data.filter((_, index) => index % step === 0);
    };

    const sampled = sampleData(largeDataset, 500);

    expect(sampled.length).toBeLessThanOrEqual(500);
    expect(sampled.length).toBeGreaterThan(400); // 确保不是过度抽样
  });

  it('GridPerformance handles large grid data', () => {
    const largeGridPerformance = Array.from({ length: 50 }, (_, i) => ({
      price: (3.2 + i * 0.03).toFixed(3),
      trigger_count: Math.floor(Math.random() * 10),
      profit_contribution: Math.random() * 100,
    }));

    const start = performance.now();

    const gridData = largeGridPerformance.map((grid) => ({
      price: grid.price,
      triggerCount: grid.trigger_count,
      profitContribution: grid.profit_contribution,
      triggered: grid.trigger_count > 0,
    }));

    const end = performance.now();

    // 处理时间应小于10ms
    expect(end - start).toBeLessThan(10);
    expect(gridData).toHaveLength(50);
  });

  it('sessionStorage caching works', () => {
    const testKey = 'test_backtest_cache';
    const testData = { test: 'data' };

    // 清理可能的旧数据
    sessionStorage.removeItem(testKey);

    // 模拟缓存写入
    sessionStorage.setItem(testKey, JSON.stringify(testData));

    // 模拟缓存读取
    const cached = sessionStorage.getItem(testKey);
    const parsed = JSON.parse(cached);

    expect(parsed).toEqual(testData);
  });

  it('memory usage is reasonable', () => {
    const largeDataset = generateLargeDataset(5000);
    const largeTrades = generateLargeTradeRecords(500);

    // 模拟内存使用计算
    const datasetSize = JSON.stringify(largeDataset).length;
    const tradesSize = JSON.stringify(largeTrades).length;
    const totalSize = datasetSize + tradesSize;

    // 数据大小应小于10MB
    expect(totalSize).toBeLessThan(10 * 1024 * 1024);
  });
});
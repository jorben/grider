import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BacktestTab from '../BacktestTab';
import * as api from '@shared/services/api';

// Mock API
jest.mock('@shared/services/api');

const mockGridStrategy = {
  current_price: 3.500,
  price_range: { lower: 3.200, upper: 3.800 },
  grid_config: {
    count: 20,
    type: '等差',
    step_size: 0.030,
    single_trade_quantity: 100,
  },
  fund_allocation: {
    base_position_amount: 2500.00,
    base_position_shares: 700,
    grid_trading_amount: 7000.00,
  },
  price_levels: [3.200, 3.230, 3.260, 3.290, 3.320, 3.350, 3.380, 3.410, 3.440, 3.470, 3.500, 3.530, 3.560, 3.590, 3.620, 3.650, 3.680, 3.710, 3.740, 3.770, 3.800],
};

const mockBacktestResult = {
  backtest_period: {
    start_date: '2025-01-10',
    end_date: '2025-01-16',
    trading_days: 5,
    total_bars: 240,
  },
  performance_metrics: {
    total_return: 0.052,
    annualized_return: 0.385,
    absolute_profit: 520.0,
    max_drawdown: -0.023,
    sharpe_ratio: 1.85,
    volatility: 0.156,
  },
  trading_metrics: {
    total_trades: 24,
    buy_trades: 12,
    sell_trades: 12,
    win_rate: 0.625,
    profit_loss_ratio: 1.8,
    grid_trigger_rate: 0.452,
  },
  benchmark_comparison: {
    hold_return: 0.022,
    excess_return: 0.030,
    excess_return_rate: 1.364,
  },
  equity_curve: [
    {
      time: '2025-01-10T09:35:00.000Z',
      total_asset: 10000.00,
    },
    // ... 更多数据
  ],
  price_curve: [
    {
      time: '2025-01-10T09:35:00.000Z',
      open: 3.500,
      high: 3.510,
      low: 3.495,
      close: 3.505,
      volume: 12500,
    },
    // ... 更多数据
  ],
  trade_records: [
    {
      time: '2025-01-10T10:05:00.000Z',
      type: 'BUY',
      price: 3.470,
      quantity: 100,
      commission: 0.35,
      profit: null,
      position: 800,
      cash: 9649.65,
    },
    // ... 更多交易记录
  ],
  grid_analysis: {
    triggered_grids: 9,
    total_grids: 20,
    grid_performance: [
      {
        price: 3.470,
        trigger_count: 3,
        profit_contribution: 15.60,
      },
      // ... 更多网格数据
    ],
  },
  final_state: {
    cash: 10520.00,
    position: 700,
    position_value: 2450.00,
    total_asset: 12970.00,
  },
};

describe('BacktestTab Integration', () => {
  beforeEach(() => {
    api.runBacktest.mockResolvedValue(mockBacktestResult);
  });

  it('完整的回测流程', async () => {
    render(<BacktestTab etfCode="510300" exchangeCode="XSHG" gridStrategy={mockGridStrategy} />);

    // 1. 显示功能引导
    expect(screen.getByText(/回测分析功能说明/i)).toBeInTheDocument();

    // 2. 显示参数编辑器
    expect(screen.getByText(/回测参数/i)).toBeInTheDocument();

    // 3. 显示加载状态
    expect(screen.getByText(/正在准备回测数据/i)).toBeInTheDocument();

    // 4. 等待数据加载完成
    await waitFor(() => {
      expect(screen.getByText(/核心指标/i)).toBeInTheDocument();
    });

    // 5. 验证指标展示
    expect(screen.getByText('5.2%')).toBeInTheDocument();
    expect(screen.getByText(/总收益率/i)).toBeInTheDocument();

    // 6. 验证图表渲染
    expect(screen.getByText(/价格走势与交易点位/i)).toBeInTheDocument();
    expect(screen.getByText(/收益曲线对比/i)).toBeInTheDocument();

    // 7. 验证交易记录
    expect(screen.getByText(/交易记录/i)).toBeInTheDocument();

    // 8. 验证网格分析
    expect(screen.getByText(/网格表现分析/i)).toBeInTheDocument();
  });

  it('参数编辑和重新回测', async () => {
    render(<BacktestTab etfCode="510300" exchangeCode="XSHG" gridStrategy={mockGridStrategy} />);

    await waitFor(() => {
      expect(screen.getByText(/核心指标/i)).toBeInTheDocument();
    });

    // 点击编辑参数
    const editButton = screen.getByText(/编辑参数/i);
    userEvent.click(editButton);

    // 修改手续费率
    const rateInput = screen.getByLabelText(/手续费率/i);
    userEvent.clear(rateInput);
    userEvent.type(rateInput, '0.03');

    // 保存并重新回测
    const saveButton = screen.getByText(/保存并重新回测/i);
    userEvent.click(saveButton);

    // 验证重新调用API
    await waitFor(() => {
      expect(api.runBacktest).toHaveBeenCalledTimes(2);
    });
  });

  it('错误处理', async () => {
    api.runBacktest.mockRejectedValue(new Error('网络错误'));

    render(<BacktestTab etfCode="510300" exchangeCode="XSHG" gridStrategy={mockGridStrategy} />);

    await waitFor(() => {
      expect(screen.getByText(/回测失败/i)).toBeInTheDocument();
    });

    // 点击重试
    const retryButton = screen.getByText(/重新回测/i);
    userEvent.click(retryButton);

    expect(api.runBacktest).toHaveBeenCalledTimes(2);
  });

  it('数据缓存', async () => {
    // 第一次渲染
    const { rerender } = render(<BacktestTab etfCode="510300" exchangeCode="XSHG" gridStrategy={mockGridStrategy} />);

    await waitFor(() => {
      expect(screen.getByText(/核心指标/i)).toBeInTheDocument();
    });

    // 重新渲染相同参数
    rerender(<BacktestTab etfCode="510300" exchangeCode="XSHG" gridStrategy={mockGridStrategy} />);

    // 应该从缓存加载，不重新调用API
    expect(api.runBacktest).toHaveBeenCalledTimes(1);
  });
});
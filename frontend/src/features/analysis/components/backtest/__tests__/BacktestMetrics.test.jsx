import React from 'react';
import { render, screen } from '@testing-library/react';
import BacktestMetrics from '../BacktestMetrics';

const mockData = {
  metrics: {
    total_return: 0.052,
    annualized_return: 0.385,
    absolute_profit: 520.0,
    max_drawdown: -0.023,
    sharpe_ratio: 1.85,
    volatility: 0.156,
  },
  tradingMetrics: {
    total_trades: 24,
    buy_trades: 12,
    sell_trades: 12,
    win_rate: 0.625,
    profit_loss_ratio: 1.8,
    grid_trigger_rate: 0.452,
  },
  benchmark: {
    hold_return: 0.022,
    excess_return: 0.03,
    excess_return_rate: 1.364,
  },
  period: {
    start_date: '2025-01-10',
    end_date: '2025-01-16',
    trading_days: 5,
    total_bars: 240,
  },
};

describe('BacktestMetrics', () => {
  it('renders core metrics correctly', () => {
    render(<BacktestMetrics {...mockData} />);

    expect(screen.getByText('总收益率')).toBeInTheDocument();
    expect(screen.getByText('5.2%')).toBeInTheDocument();
    expect(screen.getByText('年化收益')).toBeInTheDocument();
  });

  it('displays benchmark comparison', () => {
    render(<BacktestMetrics {...mockData} />);

    expect(screen.getByText('基准对比')).toBeInTheDocument();
    expect(screen.getByText('持有不动')).toBeInTheDocument();
    expect(screen.getByText('超额收益')).toBeInTheDocument();
  });

  it('shows trading statistics', () => {
    render(<BacktestMetrics {...mockData} />);

    expect(screen.getByText('交易统计')).toBeInTheDocument();
    expect(screen.getByText('24次')).toBeInTheDocument();
    expect(screen.getByText('62.5%')).toBeInTheDocument();
  });
});
'use client';

import { useQuery } from '@tanstack/react-query';
import { mockPerformanceData, simulateApiDelay } from './mockData';

interface PerformanceData {
  annual_return: number;
  total_return: number;
  max_drawdown: number;
  sharpe_ratio: number;
  calmar_ratio: number;
  volatility: number;
  total_trades: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Performance Metrics Component
 *
 * Displays detailed performance statistics in a card layout
 * Following the dark theme with neutral colors
 */
export default function PerformanceMetrics() {
  const {
    data: performance,
    isLoading,
    error,
  } = useQuery<PerformanceData>({
    queryKey: ['backtest-performance'],
    queryFn: async () => {
      try {
        const response = await fetch(`${API_BASE}/api/v1/backtest/page/performance`);
        if (!response.ok) {
          throw new Error(`API not available: ${response.status}`);
        }
        return response.json();
      } catch (error) {
        // Fallback to mock data for development
        console.log('Using mock data for performance metrics (API not available)');
        await simulateApiDelay();
        return mockPerformanceData;
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  if (isLoading) {
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-neutral-700 rounded mb-4 w-48"></div>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <div key={i} className="flex justify-between">
                <div className="h-4 bg-neutral-700 rounded w-32"></div>
                <div className="h-4 bg-neutral-700 rounded w-16"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-red-400 mb-4">Performance Metrics</h3>
        <p className="text-neutral-400 text-sm">Error loading performance data: {error.message}</p>
      </div>
    );
  }

  if (!performance) {
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-neutral-300 mb-4">Performance Metrics</h3>
        <p className="text-neutral-400 text-sm">No performance data available</p>
      </div>
    );
  }

  const formatPercent = (value: number, decimals = 1) => `${(value * 100).toFixed(decimals)}%`;

  const formatNumber = (value: number, decimals = 2) => value.toFixed(decimals);

  const formatCurrency = (value: number, decimals = 2) => `$${value.toFixed(decimals)}`;

  const metrics = [
    {
      label: 'Total Return',
      value: formatPercent(performance.total_return),
      color: performance.total_return > 0 ? 'text-green-400' : 'text-red-400',
    },
    {
      label: 'Annual Return',
      value: formatPercent(performance.annual_return),
      color: performance.annual_return > 0 ? 'text-green-400' : 'text-red-400',
    },
    {
      label: 'Max Drawdown',
      value: formatPercent(performance.max_drawdown),
      color: 'text-red-400',
    },
    {
      label: 'Volatility',
      value: formatPercent(performance.volatility),
      color: 'text-neutral-300',
    },
    {
      label: 'Sharpe Ratio',
      value: formatNumber(performance.sharpe_ratio),
      color: performance.sharpe_ratio > 1 ? 'text-green-400' : 'text-neutral-300',
    },
    {
      label: 'Calmar Ratio',
      value: formatNumber(performance.calmar_ratio),
      color: performance.calmar_ratio > 1 ? 'text-green-400' : 'text-neutral-300',
    },
    {
      label: 'Total Trades',
      value: performance.total_trades.toLocaleString(),
      color: 'text-blue-400',
    },
    {
      label: 'Win Rate',
      value: formatPercent(performance.win_rate),
      color: performance.win_rate > 0.5 ? 'text-green-400' : 'text-red-400',
    },
    {
      label: 'Average Win',
      value: formatCurrency(performance.avg_win),
      color: 'text-green-400',
    },
    {
      label: 'Average Loss',
      value: formatCurrency(performance.avg_loss),
      color: 'text-red-400',
    },
    {
      label: 'Profit Factor',
      value: formatNumber(performance.profit_factor),
      color: performance.profit_factor > 1 ? 'text-green-400' : 'text-red-400',
    },
  ];

  return (
    <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-6">Performance Metrics</h3>

      <div className="space-y-4">
        {metrics.map((metric, index) => (
          <div key={index} className="flex justify-between items-center">
            <span className="text-neutral-400 text-sm">{metric.label}</span>
            <span className={`font-medium ${metric.color}`}>{metric.value}</span>
          </div>
        ))}
      </div>

      {/* Performance Summary */}
      <div className="mt-6 pt-4 border-t border-neutral-700">
        <div className="text-xs text-neutral-500">
          Strategy demonstrates{' '}
          <span className={performance.annual_return > 0.1 ? 'text-green-400' : 'text-red-400'}>
            {performance.annual_return > 0.1 ? 'strong' : 'weak'}
          </span>{' '}
          performance with{' '}
          <span className={performance.sharpe_ratio > 1.5 ? 'text-green-400' : 'text-neutral-300'}>
            {performance.sharpe_ratio > 1.5 ? 'excellent' : 'moderate'}
          </span>{' '}
          risk-adjusted returns
        </div>
      </div>
    </div>
  );
}

'use client';

import { useQuery } from '@tanstack/react-query';
import type { PerformanceData } from '../../lib/backtestDataLoader';
import { getPerformanceData, simulateApiDelay } from '../../lib/backtestDataLoader';

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
      console.log('Loading performance data from local data');
      await simulateApiDelay();
      return getPerformanceData();
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

  // Use the top performing strategy for metrics display
  const topStrategy = performance.top_performing_strategies?.[0];
  if (!topStrategy) {
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-6">Performance Metrics</h3>
        <p className="text-neutral-400 text-sm">No performance data available</p>
      </div>
    );
  }

  const metrics = [
    {
      label: 'Annual Return',
      value: topStrategy.performance_metrics.annual_return_pct,
      color:
        parseFloat(topStrategy.performance_metrics.annual_return_pct) > 0
          ? 'text-green-400'
          : 'text-red-400',
    },
    {
      label: 'Max Drawdown',
      value: topStrategy.performance_metrics.max_drawdown_pct,
      color: 'text-red-400',
    },
    {
      label: 'Sharpe Ratio',
      value: formatNumber(topStrategy.performance_metrics.sharpe_ratio),
      color:
        topStrategy.performance_metrics.sharpe_ratio > 1 ? 'text-green-400' : 'text-neutral-300',
    },
    {
      label: 'Win Rate',
      value: topStrategy.performance_metrics.win_rate_pct,
      color: topStrategy.performance_metrics.win_rate > 50 ? 'text-green-400' : 'text-red-400',
    },
    {
      label: 'Strategy',
      value: topStrategy.strategy,
      color: 'text-blue-400',
    },
    {
      label: 'Currency Pair',
      value: topStrategy.currency_pair,
      color: 'text-neutral-300',
    },
    {
      label: 'Timeframe',
      value: topStrategy.timeframe,
      color: 'text-neutral-300',
    },
    {
      label: 'Category',
      value: topStrategy.category,
      color: 'text-purple-400',
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
          Top strategy ({topStrategy.strategy}) demonstrates{' '}
          <span
            className={
              topStrategy.performance_metrics.annual_return > 0.1
                ? 'text-green-400'
                : 'text-red-400'
            }
          >
            {topStrategy.performance_metrics.annual_return > 0.1 ? 'strong' : 'weak'}
          </span>{' '}
          performance with{' '}
          <span
            className={
              topStrategy.performance_metrics.sharpe_ratio > 1.5
                ? 'text-green-400'
                : 'text-neutral-300'
            }
          >
            {topStrategy.performance_metrics.sharpe_ratio > 1.5 ? 'excellent' : 'moderate'}
          </span>{' '}
          risk-adjusted returns
        </div>
      </div>
    </div>
  );
}

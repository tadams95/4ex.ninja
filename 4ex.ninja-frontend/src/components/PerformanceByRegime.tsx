/**
 * PerformanceByRegime Component
 * Displays strategy performance metrics and summary
 */

'use client';

import React from 'react';
import { type PerformanceSummary } from '../hooks/useRegimeData';
import { Card } from './ui/Card';

interface PerformanceByRegimeProps {
  performanceSummary: PerformanceSummary | null;
  loading: boolean;
}

const formatPercentage = (value: number): string => {
  return `${(value * 100).toFixed(2)}%`;
};

const formatNumber = (value: number): string => {
  return value.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};

const MetricCard: React.FC<{
  title: string;
  value: string;
  color?: 'green' | 'red' | 'yellow' | 'blue' | 'neutral';
  subtitle?: string;
}> = ({ title, value, color = 'neutral', subtitle }) => {
  const colorClasses = {
    green: 'text-green-400',
    red: 'text-red-400',
    yellow: 'text-yellow-400',
    blue: 'text-blue-400',
    neutral: 'text-white',
  };

  return (
    <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-4 transition-colors hover:bg-neutral-750">
      <div className="text-xs text-neutral-400 uppercase tracking-wide mb-2">{title}</div>
      <div className={`text-xl font-bold ${colorClasses[color]} mb-1`}>{value}</div>
      {subtitle && <div className="text-xs text-neutral-500">{subtitle}</div>}
    </div>
  );
};

export const PerformanceByRegime: React.FC<PerformanceByRegimeProps> = ({
  performanceSummary,
  loading,
}) => {
  if (loading) {
    return (
      <Card variant="elevated" padding="lg" className="animate-pulse">
        <div className="h-6 bg-neutral-600 rounded mb-6"></div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-20 bg-neutral-600 rounded"></div>
          ))}
        </div>
      </Card>
    );
  }

  if (!performanceSummary) {
    return (
      <Card variant="outlined" padding="lg" className="border-red-500/30">
        <h3 className="text-lg font-semibold text-red-400 mb-2">Performance Data Unavailable</h3>
        <p className="text-neutral-400">
          Unable to fetch performance metrics. Please check your API connection and try refreshing.
        </p>
      </Card>
    );
  }

  const getReturnColor = (value: number) => {
    if (value > 0) return 'green';
    if (value < 0) return 'red';
    return 'neutral';
  };

  const getWinRateColor = (value: number) => {
    if (value >= 0.6) return 'green';
    if (value >= 0.4) return 'yellow';
    return 'red';
  };

  const getSharpeColor = (value: number) => {
    if (value >= 1.5) return 'green';
    if (value >= 1.0) return 'yellow';
    if (value >= 0.5) return 'blue';
    return 'red';
  };

  return (
    <Card variant="elevated" padding="lg" className="border border-neutral-600">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-white">Strategy Performance</h3>
        <div className="flex items-center space-x-2">
          <div
            className={`w-2 h-2 rounded-full ${
              performanceSummary.current_positions > 0
                ? 'bg-green-500 animate-pulse'
                : 'bg-gray-500'
            }`}
          ></div>
          <span className="text-xs text-neutral-400">
            {performanceSummary.current_positions} Active Position
            {performanceSummary.current_positions !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
        <MetricCard
          title="Total Return"
          value={formatPercentage(performanceSummary.total_return)}
          color={getReturnColor(performanceSummary.total_return)}
        />

        <MetricCard
          title="Sharpe Ratio"
          value={formatNumber(performanceSummary.sharpe_ratio)}
          color={getSharpeColor(performanceSummary.sharpe_ratio)}
          subtitle="Risk-adjusted return"
        />

        <MetricCard
          title="Max Drawdown"
          value={formatPercentage(Math.abs(performanceSummary.max_drawdown))}
          color={performanceSummary.max_drawdown > -0.2 ? 'green' : 'red'}
          subtitle="Peak to trough"
        />

        <MetricCard
          title="Win Rate"
          value={formatPercentage(performanceSummary.win_rate)}
          color={getWinRateColor(performanceSummary.win_rate)}
        />

        <MetricCard
          title="Total Trades"
          value={performanceSummary.total_trades.toString()}
          color="blue"
        />

        <MetricCard
          title="Avg Duration"
          value={`${performanceSummary.avg_trade_duration.toFixed(1)}h`}
          color="neutral"
          subtitle="Per trade"
        />
      </div>

      {/* Summary Status */}
      <div className="p-4 bg-neutral-800 border border-neutral-700 rounded-lg">
        <div className="flex items-center justify-between">
          <span className="text-sm text-neutral-400 font-medium">Strategy Status</span>
          <div className="flex items-center space-x-2">
            {performanceSummary.total_trades === 0 ? (
              <>
                <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-yellow-400 font-medium">Waiting for trades</span>
              </>
            ) : performanceSummary.total_return > 0 ? (
              <>
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm text-green-400 font-medium">Profitable</span>
              </>
            ) : (
              <>
                <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                <span className="text-sm text-red-400 font-medium">Loss-making</span>
              </>
            )}
          </div>
        </div>
        {performanceSummary.total_trades > 0 && (
          <div className="mt-2 text-xs text-neutral-500">
            Performance based on {performanceSummary.total_trades} completed trades
          </div>
        )}
      </div>
    </Card>
  );
};

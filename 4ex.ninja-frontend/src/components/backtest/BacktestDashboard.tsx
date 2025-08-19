'use client';

import { useQuery } from '@tanstack/react-query';
import dynamic from 'next/dynamic';
import { useState } from 'react';
import { Button } from '../ui/Button';
import { mockPerformanceData, mockSummaryData, simulateApiDelay } from './mockData';

// Dynamic imports for heavy components
const PerformanceMetrics = dynamic(() => import('./PerformanceMetrics'), {
  ssr: false,
  loading: () => (
    <div className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-lg h-48" />
  ),
});

const EquityCurveChart = dynamic(() => import('./EquityCurveChart'), {
  ssr: false,
  loading: () => (
    <div className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-lg h-64" />
  ),
});

const VisualAnalytics = dynamic(() => import('./VisualAnalytics'), {
  ssr: false,
  loading: () => (
    <div className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-lg h-96" />
  ),
});

const MethodologySection = dynamic(() => import('./MethodologySection'), {
  ssr: false,
  loading: () => (
    <div className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-lg h-64" />
  ),
});

interface BacktestSummary {
  total_strategies: number;
  avg_annual_return: number;
  avg_max_drawdown: number;
  avg_sharpe_ratio: number;
  winning_percentage: number;
  timeframe: string;
  currency_pairs: string[];
}

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
 * Main Backtest Dashboard Component
 *
 * Displays comprehensive backtest results for the MA Unified Strategy
 * Following the dark theme aesthetic with responsive grid layouts
 */
export default function BacktestDashboard() {
  const [activeTab, setActiveTab] = useState<'overview' | 'analytics' | 'methodology'>('overview');

  // Fetch backtest summary
  const {
    data: summary,
    isLoading: summaryLoading,
    error: summaryError,
  } = useQuery<BacktestSummary>({
    queryKey: ['backtest-summary'],
    queryFn: async () => {
      try {
        const response = await fetch(`${API_BASE}/api/v1/backtest/page/summary`);
        if (!response.ok) {
          throw new Error(`API not available: ${response.status}`);
        }
        return response.json();
      } catch (error) {
        // Fallback to mock data for development
        console.log('Using mock data for summary (API not available)');
        await simulateApiDelay();
        return mockSummaryData;
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Fetch performance metrics
  const {
    data: performance,
    isLoading: perfLoading,
    error: perfError,
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
        console.log('Using mock data for performance (API not available)');
        await simulateApiDelay();
        return mockPerformanceData;
      }
    },
    staleTime: 5 * 60 * 1000,
  });

  if (summaryError || perfError) {
    return (
      <div className="min-h-screen bg-black text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-red-400 mb-4">Unable to Load Backtest Data</h1>
            <p className="text-neutral-400 mb-6">
              {summaryError?.message || perfError?.message || 'An unexpected error occurred'}
            </p>
            <Button variant="primary" onClick={() => window.location.reload()}>
              Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <div className="border-b border-neutral-700 bg-black">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div>
              <h1 className="text-2xl font-bold text-white">Backtest Results</h1>
              <p className="text-sm text-neutral-400">
                {summaryLoading
                  ? 'Loading...'
                  : `${summary?.timeframe || '5 years'} of proven MA Unified Strategy performance`}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {summaryLoading ? (
                <div className="px-3 py-2 text-sm bg-neutral-600 rounded-md animate-pulse">
                  Loading...
                </div>
              ) : (
                <div className="px-3 py-2 text-sm bg-green-600 rounded-md">
                  {summary?.total_strategies || 0} Strategies Tested
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-neutral-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {[
              { id: 'overview', label: 'Performance Overview', disabled: perfLoading },
              { id: 'analytics', label: 'Visual Analytics', disabled: false },
              { id: 'methodology', label: 'Methodology', disabled: false },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => !tab.disabled && setActiveTab(tab.id as any)}
                disabled={tab.disabled}
                className={`
                  py-4 px-1 border-b-2 font-medium text-sm transition-colors
                  ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-400'
                      : tab.disabled
                      ? 'border-transparent text-neutral-600 cursor-not-allowed'
                      : 'border-transparent text-neutral-400 hover:text-neutral-300 hover:border-neutral-600'
                  }
                `}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Quick Stats Grid */}
            {perfLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {[1, 2, 3, 4].map(i => (
                  <div
                    key={i}
                    className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-lg h-24"
                  />
                ))}
              </div>
            ) : (
              performance && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-4">
                    <h3 className="text-sm font-medium text-neutral-400">Annual Return</h3>
                    <p className="text-2xl font-bold text-green-400">
                      {(performance.annual_return * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-4">
                    <h3 className="text-sm font-medium text-neutral-400">Max Drawdown</h3>
                    <p className="text-2xl font-bold text-red-400">
                      {(performance.max_drawdown * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-4">
                    <h3 className="text-sm font-medium text-neutral-400">Sharpe Ratio</h3>
                    <p className="text-2xl font-bold text-blue-400">
                      {performance.sharpe_ratio.toFixed(2)}
                    </p>
                  </div>
                  <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-4">
                    <h3 className="text-sm font-medium text-neutral-400">Win Rate</h3>
                    <p className="text-2xl font-bold text-purple-400">
                      {(performance.win_rate * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              )
            )}

            {/* Performance Metrics and Equity Curve */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <PerformanceMetrics />
              <EquityCurveChart />
            </div>
          </div>
        )}

        {activeTab === 'analytics' && <VisualAnalytics />}

        {activeTab === 'methodology' && <MethodologySection />}
      </div>
    </div>
  );
}

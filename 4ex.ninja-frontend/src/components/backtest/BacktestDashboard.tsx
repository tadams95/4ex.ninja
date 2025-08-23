'use client';

import { useQuery } from '@tanstack/react-query';
import dynamic from 'next/dynamic';
import { useState } from 'react';
import type {
  ConfidenceAnalysis,
  EnhancedOptimizationResults,
} from '../../lib/secondBacktestDataLoader';
import {
  getConfidenceAnalysis,
  loadEnhancedOptimizationResults,
  simulateApiDelay,
} from '../../lib/secondBacktestDataLoader';
import { Button } from '../ui/Button';

// Dynamic imports for heavy components
const PerformanceMetrics = dynamic(() => import('./PerformanceMetrics'), {
  ssr: false,
  loading: () => (
    <div className="animate-pulse bg-neutral-900 border border-neutral-700 rounded-lg h-48" />
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

const CurrencyAnalysis = dynamic(() => import('./CurrencyAnalysis'), {
  ssr: false,
  loading: () => (
    <div className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-lg h-64" />
  ),
});

/**
 * Enhanced Daily Strategy v2.0 - Backtest Dashboard
 *
 * Professional dashboard displaying comprehensive second backtest run results
 * for the Enhanced Daily Strategy v2.0 across 10 major currency pairs
 * Features 4,436 total trades with 100% profitable pairs and confidence analysis
 */
export default function BacktestDashboard() {
  const [activeTab, setActiveTab] = useState<
    'overview' | 'analytics' | 'currencies' | 'methodology'
  >('overview');

  // Fetch enhanced optimization results from second backtest run
  const {
    data: optimizationData,
    isLoading,
    error,
  } = useQuery<EnhancedOptimizationResults>({
    queryKey: ['enhanced-optimization-results'],
    queryFn: async () => {
      console.log('Loading Enhanced Daily Strategy v2.0 optimization results');
      await simulateApiDelay();
      return loadEnhancedOptimizationResults();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Fetch confidence analysis separately
  const { data: confidenceData, isLoading: confidenceLoading } =
    useQuery<ConfidenceAnalysis | null>({
      queryKey: ['confidence-analysis'],
      queryFn: async () => {
        await simulateApiDelay(300);
        return getConfidenceAnalysis();
      },
      staleTime: 5 * 60 * 1000,
    });

  if (error) {
    return (
      <div className="min-h-screen bg-black text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-red-400 mb-4">
              Unable to Load Optimization Data
            </h1>
            <p className="text-neutral-400 mb-6">
              {error?.message || 'An unexpected error occurred while loading strategy results'}
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
      {/* Enhanced Header */}
      <div className="border-b border-neutral-700 ">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between py-6 space-y-4 lg:space-y-0">
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-white">
                  Enhanced Daily Strategy v2.0
                </h1>
                {optimizationData?.optimization_info.strategy_version && (
                  <span className="px-2 py-1 text-xs bg-blue-900/30 border border-blue-700 rounded text-blue-400">
                    {optimizationData.optimization_info.strategy_version}
                  </span>
                )}
              </div>
              <p className="text-neutral-400 text-sm mb-1">
                {isLoading
                  ? 'Loading comprehensive validation results...'
                  : optimizationData?.optimization_info.methodology ||
                    'Comprehensive 4,436-trade validation across 10 currency pairs'}
              </p>
              <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-4 space-y-1 sm:space-y-0">
                <p className="text-neutral-500 text-xs">
                  Validation Date:{' '}
                  {isLoading
                    ? 'Loading...'
                    : optimizationData?.optimization_info.date
                    ? new Date(optimizationData.optimization_info.date).toLocaleDateString(
                        'en-US',
                        {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        }
                      )
                    : 'August 21, 2025'}
                </p>
                {optimizationData?.optimization_info.total_trades && (
                  <p className="text-neutral-500 text-xs">
                    Total Trades:{' '}
                    <span className="text-blue-400 font-medium">
                      {optimizationData.optimization_info.total_trades.toLocaleString()}
                    </span>
                  </p>
                )}
              </div>
            </div>

            {/* Enhanced Key Stats Summary */}
            <div className="flex items-center justify-center lg:justify-end">
              {isLoading ? (
                <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                  {[1, 2, 3].map(i => (
                    <div
                      key={i}
                      className="px-4 py-3 bg-neutral-700 rounded-lg animate-pulse w-24 h-16"
                    ></div>
                  ))}
                </div>
              ) : (
                optimizationData && (
                  <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                    <div className="text-center px-4 py-3 bg-green-900/30 border border-green-700 rounded-lg min-w-[6rem]">
                      <div className="text-xl sm:text-2xl font-bold text-green-400">
                        {optimizationData.optimization_info.success_rate}
                      </div>
                      <div className="text-xs text-green-300">Backtest Success</div>
                      {confidenceData && (
                        <div className="text-xs text-yellow-400 mt-1">48-52% Live*</div>
                      )}
                    </div>
                    <div className="text-center px-4 py-3 bg-blue-900/30 border border-blue-700 rounded-lg min-w-[6rem]">
                      <div className="text-xl sm:text-2xl font-bold text-blue-400">
                        {optimizationData.summary_stats.avg_profit_factor?.toFixed(2) ||
                          optimizationData.summary_stats.best_return}
                      </div>
                      <div className="text-xs text-blue-300">Avg Profit Factor</div>
                    </div>
                    <div className="text-center px-4 py-3 bg-purple-900/30 border border-purple-700 rounded-lg min-w-[6rem]">
                      <div className="text-lg font-bold text-purple-400">
                        {optimizationData.summary_stats.total_trades?.toLocaleString() || 'JPY'}
                      </div>
                      <div className="text-xs text-purple-300">
                        {optimizationData.summary_stats.total_trades ? 'Total Trades' : 'Dominance'}
                      </div>
                    </div>
                  </div>
                )
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Tab Navigation */}
      <div className="border-b border-neutral-700 bg-black">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex overflow-x-auto scrollbar-hide space-x-4 sm:space-x-6 lg:space-x-8">
            {[
              {
                id: 'overview',
                label: 'Performance Overview',
                shortLabel: 'Overview',
                icon: '📊',
                disabled: isLoading,
                description: 'Key metrics and results',
              },
              {
                id: 'analytics',
                label: 'Visual Analytics',
                shortLabel: 'Analytics',
                icon: '📈',
                disabled: false,
                description: 'Charts and data visualization',
              },
              {
                id: 'currencies',
                label: 'Currency Analysis',
                shortLabel: 'Currencies',
                icon: '💱',
                disabled: false,
                description: 'Pair-by-pair breakdown',
              },
              {
                id: 'methodology',
                label: 'Strategy Details',
                shortLabel: 'Strategy',
                icon: '⚙️',
                disabled: false,
                description: 'Implementation and methodology',
              },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => !tab.disabled && setActiveTab(tab.id as any)}
                disabled={tab.disabled}
                className={`
                  group py-4 px-2 sm:px-3 border-b-2 font-medium text-sm transition-all duration-200 whitespace-nowrap min-w-0 flex-shrink-0
                  ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-400'
                      : tab.disabled
                      ? 'border-transparent text-neutral-600 cursor-not-allowed'
                      : 'border-transparent text-neutral-400 hover:text-neutral-300 hover:border-neutral-600'
                  }
                `}
              >
                <div className="flex items-center space-x-2 min-h-[44px]">
                  <span className="text-base">{tab.icon}</span>
                  <span className="hidden sm:inline">{tab.label}</span>
                  <span className="sm:hidden">{tab.shortLabel}</span>
                </div>
                <div className="text-xs text-neutral-500 group-hover:text-neutral-400 mt-1 hidden md:block">
                  {tab.description}
                </div>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <OverviewTab
            optimizationData={optimizationData}
            confidenceData={confidenceData}
            isLoading={isLoading}
          />
        )}
        {activeTab === 'analytics' && <VisualAnalytics />}
        {activeTab === 'currencies' && <CurrencyAnalysis />}
        {activeTab === 'methodology' && <MethodologySection />}
      </div>
    </div>
  );
}

/**
 * Enhanced Overview Tab Component
 */
interface OverviewTabProps {
  optimizationData?: EnhancedOptimizationResults;
  confidenceData?: ConfidenceAnalysis | null;
  isLoading: boolean;
}

function OverviewTab({ optimizationData, confidenceData, isLoading }: OverviewTabProps) {
  if (isLoading) {
    return (
      <div className="space-y-8">
        {/* Loading Hero Section */}
        <div className="animate-pulse">
          <div className="h-8 bg-neutral-700 rounded mb-4 w-96"></div>
          <div className="h-4 bg-neutral-800 rounded mb-6 w-full max-w-2xl"></div>
        </div>

        {/* Loading Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map(i => (
            <div
              key={i}
              className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-lg h-32"
            />
          ))}
        </div>

        {/* Loading Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-lg h-96" />
          <div className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-lg h-96" />
        </div>
      </div>
    );
  }

  if (!optimizationData) {
    return (
      <div className="text-center py-12">
        <h3 className="text-xl font-medium text-neutral-400 mb-4">No Data Available</h3>
        <p className="text-neutral-500">Unable to load optimization results</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Confidence Disclaimer Banner */}
      {confidenceData && (
        <div className="bg-gradient-to-r from-yellow-900/20 to-orange-900/20 border border-yellow-700 rounded-xl p-4">
          <div className="flex items-start space-x-3">
            <div className="text-2xl">⚠️</div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-yellow-400 mb-2">
                Live Trading Reality Check
              </h3>
              <p className="text-neutral-300 text-sm mb-3">
                While backtest shows 100% profitable pairs, realistic live trading expectations are
                48-52% win rates due to spreads, slippage, and market regime changes.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div className="bg-neutral-800/50 rounded-lg p-3">
                  <div className="text-green-400 font-medium">High Confidence (85-95%)</div>
                  <div className="text-neutral-400 mt-1">
                    Strategy methodology, data quality, JPY dominance
                  </div>
                </div>
                <div className="bg-neutral-800/50 rounded-lg p-3">
                  <div className="text-yellow-400 font-medium">Moderate Confidence (70-80%)</div>
                  <div className="text-neutral-400 mt-1">
                    Directional profitability, pair rankings
                  </div>
                </div>
                <div className="bg-neutral-800/50 rounded-lg p-3">
                  <div className="text-red-400 font-medium">Low Confidence (40-60%)</div>
                  <div className="text-neutral-400 mt-1">
                    Exact performance replication in live trading
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Strategy Overview Hero */}
      <div className=" border border-neutral-700 rounded-xl p-4 sm:p-6 lg:p-8">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between space-y-4 lg:space-y-0">
          <div className="flex-1">
            <h2 className="text-xl sm:text-2xl font-bold text-white mb-3">
              Strategy Performance Summary
            </h2>
            <p className="text-neutral-300 mb-4 text-sm sm:text-base max-w-3xl">
              Comprehensive validation results for the Enhanced Daily Strategy v2.0 across{' '}
              {optimizationData.optimization_info.total_pairs_tested} major currency pairs. Our
              systematic approach achieved {optimizationData.optimization_info.success_rate}{' '}
              backtest success rate across{' '}
              {optimizationData.optimization_info.total_trades?.toLocaleString()} total trades, with
              realistic live trading expectations of 48-52% win rates.
            </p>
            <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-6 space-y-2 sm:space-y-0 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-neutral-400">
                  Profitable Pairs: {Object.keys(optimizationData.profitable_pairs).length}/10
                  (Backtest)
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                <span className="text-neutral-400">Expected Live: 4-6 pairs profitable</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span className="text-neutral-400">
                  {optimizationData.summary_stats.jpy_dominance}
                </span>
              </div>
            </div>
          </div>
          <div className="text-center lg:text-right">
            <div className="text-2xl sm:text-3xl font-bold text-green-400 mb-1">
              {optimizationData.summary_stats.avg_profit_factor?.toFixed(2)}x
            </div>
            <div className="text-sm text-neutral-400">Avg Profit Factor</div>
            <div className="text-lg font-semibold text-blue-400 mt-2">
              {optimizationData.summary_stats.top_performer}
            </div>
            <div className="text-xs text-neutral-500">Top Performing Pair</div>
            {optimizationData.summary_stats.total_trades && (
              <div className="mt-3 text-sm text-purple-400 font-medium">
                {optimizationData.summary_stats.total_trades.toLocaleString()} trades
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Enhanced Key Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <MetricCard
          icon="🎯"
          title="Backtest Success Rate"
          value={optimizationData.optimization_info.success_rate}
          subtitle={`All ${optimizationData.optimization_info.total_pairs_tested} pairs profitable in backtest`}
          color="green"
          trend="neutral"
        />

        <MetricCard
          icon="⚠️"
          title="Live Trading Expectation"
          value="48-52%"
          subtitle="Realistic win rate with real costs"
          color="yellow"
          trend="down"
        />

        <MetricCard
          icon="🥇"
          title="Average Profit Factor"
          value={`${optimizationData.summary_stats.avg_profit_factor?.toFixed(2)}x`}
          subtitle={`Range: 3.1x - 4.14x across pairs`}
          color="blue"
          trend="up"
        />

        <MetricCard
          icon="📊"
          title="Total Validation Trades"
          value={optimizationData.summary_stats.total_trades?.toLocaleString() || '4,436'}
          subtitle="Comprehensive 5-year historical test"
          color="purple"
          trend="up"
        />
      </div>

      {/* Performance Breakdown Section */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 lg:gap-8">
        {/* Profitable Pairs */}
        <div className="xl:col-span-2">
          <ProfitablePairsSection profitable_pairs={optimizationData.profitable_pairs} />
        </div>

        {/* Unprofitable Pairs */}
        <div>
          <UnprofitablePairsSection unprofitable_pairs={optimizationData.unprofitable_pairs} />
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
        <PerformanceMetrics />
        <EquityCurveChart />
      </div>
    </div>
  );
}

/**
 * Enhanced Metric Card Component
 */
interface MetricCardProps {
  icon: string;
  title: string;
  value: string;
  subtitle: string;
  color: 'green' | 'blue' | 'purple' | 'yellow' | 'red';
  trend: 'up' | 'down' | 'neutral';
}

function MetricCard({ icon, title, value, subtitle, color, trend }: MetricCardProps) {
  const colorClasses = {
    green: 'bg-green-900/20 border-green-700 text-green-400',
    blue: 'bg-blue-900/20 border-blue-700 text-blue-400',
    purple: 'bg-purple-900/20 border-purple-700 text-purple-400',
    yellow: 'bg-yellow-900/20 border-yellow-700 text-yellow-400',
    red: 'bg-red-900/20 border-red-700 text-red-400',
  };

  const trendIcons = {
    up: '📈',
    down: '📉',
    neutral: '➡️',
  };

  return (
    <div
      className={`p-6 rounded-xl border transition-all duration-200 hover:scale-105 ${colorClasses[color]}`}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="text-2xl">{icon}</div>
        <div className="text-sm">{trendIcons[trend]}</div>
      </div>
      <div className="space-y-2">
        <h3 className="text-sm font-medium text-neutral-400">{title}</h3>
        <div className={`text-3xl font-bold`}>{value}</div>
        <p className="text-xs text-neutral-500">{subtitle}</p>
      </div>
    </div>
  );
}

/**
 * Profitable Pairs Section
 */
interface ProfitablePairsSectionProps {
  profitable_pairs: EnhancedOptimizationResults['profitable_pairs'];
}

function ProfitablePairsSection({ profitable_pairs }: ProfitablePairsSectionProps) {
  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'HIGHLY_PROFITABLE':
        return 'bg-green-900/30 border-green-700 text-green-300';
      case 'PROFITABLE':
        return 'bg-blue-900/30 border-blue-700 text-blue-300';
      case 'MARGINALLY_PROFITABLE':
        return 'bg-yellow-900/30 border-yellow-700 text-yellow-300';
      default:
        return 'bg-neutral-800 border-neutral-700 text-neutral-300';
    }
  };

  const getTierIcon = (tier: string) => {
    switch (tier) {
      case 'HIGHLY_PROFITABLE':
        return '🥇';
      case 'PROFITABLE':
        return '🥈';
      case 'MARGINALLY_PROFITABLE':
        return '🥉';
      default:
        return '📊';
    }
  };

  return (
    <div className="bg-neutral-800 border border-neutral-700 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-white flex items-center space-x-2">
          <span>✅</span>
          <span>Profitable Currency Pairs</span>
        </h3>
        <div className="text-sm text-green-400 font-medium">
          {Object.keys(profitable_pairs).length} pairs
        </div>
      </div>

      <div className="space-y-4">
        {Object.entries(profitable_pairs)
          .sort(
            (a, b) =>
              parseFloat(b[1].annual_return.replace('%', '')) -
              parseFloat(a[1].annual_return.replace('%', ''))
          )
          .map(([pair, data]) => (
            <div
              key={pair}
              className={`p-4 rounded-lg border transition-all duration-200 hover:scale-102 ${getTierColor(
                data.tier
              )}`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <span className="text-lg">{getTierIcon(data.tier)}</span>
                  <div>
                    <h4 className="font-bold text-white text-lg">{pair}</h4>
                    <p className="text-xs text-neutral-400">{data.tier.replace(/_/g, ' ')}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-green-400">{data.annual_return}</div>
                  <div className="text-xs text-neutral-400">Annual Return</div>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                <div>
                  <div className="text-neutral-400">Win Rate</div>
                  <div className="font-semibold">{data.win_rate}</div>
                </div>
                <div>
                  <div className="text-neutral-400">Profit Factor</div>
                  <div className="font-semibold text-blue-400">{data.profit_factor}x</div>
                </div>
                <div>
                  <div className="text-neutral-400">Total Trades</div>
                  <div className="font-semibold">{data.total_trades}</div>
                </div>
                <div>
                  <div className="text-neutral-400">Total Pips</div>
                  <div className="font-semibold text-green-400">
                    {Math.round(data.total_pips).toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Trading Costs Breakdown */}
              <div className="mt-3 pt-3 border-t border-neutral-600">
                <div className="flex justify-between text-xs">
                  <span className="text-neutral-400">
                    Gross Return:{' '}
                    <span className="text-green-400">{data.gross_return.toFixed(1)}%</span>
                  </span>
                  <span className="text-neutral-400">
                    Trading Costs:{' '}
                    <span className="text-red-400">-{data.trading_costs.toFixed(1)}%</span>
                  </span>
                  <span className="text-neutral-400">
                    Net Return: <span className="text-blue-400">{data.net_return.toFixed(1)}%</span>
                  </span>
                </div>
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}

/**
 * Unprofitable Pairs Section
 */
interface UnprofitablePairsSectionProps {
  unprofitable_pairs: EnhancedOptimizationResults['unprofitable_pairs'];
}

function UnprofitablePairsSection({ unprofitable_pairs }: UnprofitablePairsSectionProps) {
  return (
    <div className="bg-neutral-800 border border-neutral-700 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-white flex items-center space-x-2">
          <span>❌</span>
          <span>Unprofitable Pairs</span>
        </h3>
        <div className="text-sm text-red-400 font-medium">
          {Object.keys(unprofitable_pairs).length} pairs
        </div>
      </div>

      <div className="space-y-3">
        {Object.entries(unprofitable_pairs)
          .sort(
            (a, b) =>
              parseFloat(a[1].annual_return.replace('%', '')) -
              parseFloat(b[1].annual_return.replace('%', ''))
          )
          .map(([pair, data]) => (
            <div key={pair} className="p-4 bg-red-900/10 border border-red-800 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3">
                  <span className="text-lg">💔</span>
                  <div>
                    <h4 className="font-bold text-white">{pair}</h4>
                    <p className="text-xs text-red-400">{data.reason}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xl font-bold text-red-400">{data.annual_return}</div>
                  <div className="text-xs text-neutral-400">Annual Return</div>
                </div>
              </div>

              <div className="flex justify-between text-sm">
                <div>
                  <div className="text-neutral-400">Win Rate</div>
                  <div className="font-semibold text-red-300">{data.win_rate}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-neutral-500">Failed after trading costs</div>
                </div>
              </div>
            </div>
          ))}
      </div>

      {/* Insights */}
      <div className="mt-6 p-4 bg-neutral-900 border border-neutral-600 rounded-lg">
        <h4 className="text-sm font-medium text-neutral-300 mb-2">💡 Key Insights</h4>
        <ul className="text-xs text-neutral-400 space-y-1">
          <li>• Non-JPY pairs struggled with consistency</li>
          <li>• Trading costs significantly impacted marginal strategies</li>
          <li>• Low win rates (below 30%) proved unsustainable</li>
        </ul>
      </div>
    </div>
  );
}

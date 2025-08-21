'use client';

import { useQuery } from '@tanstack/react-query';
import dynamic from 'next/dynamic';
import { useState } from 'react';
import type { OptimizationResults } from '../../lib/realOptimizationDataLoader';
import { loadOptimizationResults, simulateApiDelay } from '../../lib/realOptimizationDataLoader';
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
 * Enhanced Daily EMA Strategy - Backtest Dashboard
 *
 * Professional dashboard displaying comprehensive optimization results
 * for the Enhanced Daily EMA Strategy across 10 major currency pairs
 */
export default function BacktestDashboard() {
  const [activeTab, setActiveTab] = useState<
    'overview' | 'analytics' | 'currencies' | 'methodology'
  >('overview');

  // Fetch optimization results from verified data
  const {
    data: optimizationData,
    isLoading,
    error,
  } = useQuery<OptimizationResults>({
    queryKey: ['optimization-results'],
    queryFn: async () => {
      console.log('Loading Enhanced Daily EMA Strategy optimization results');
      await simulateApiDelay();
      return loadOptimizationResults();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
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
          <div className="flex items-center justify-between py-6">
            <div>
              <div className="flex items-center space-x-3 mb-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <h1 className="text-3xl font-bold text-white">Enhanced Daily EMA Strategy</h1>
              </div>
              <p className="text-neutral-400 text-sm mb-1">
                {isLoading
                  ? 'Loading optimization results...'
                  : optimizationData?.optimization_info.methodology ||
                    'Comprehensive backtesting results'}
              </p>
              <p className="text-neutral-500 text-xs">
                Optimization Date:{' '}
                {isLoading
                  ? 'Loading...'
                  : optimizationData?.optimization_info.date
                  ? new Date(optimizationData.optimization_info.date).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })
                  : 'August 20, 2025'}
              </p>
            </div>

            {/* Key Stats Summary */}
            <div className="flex items-center space-x-6">
              {isLoading ? (
                <div className="flex space-x-4">
                  {[1, 2, 3].map(i => (
                    <div
                      key={i}
                      className="px-4 py-3 bg-neutral-700 rounded-lg animate-pulse w-24 h-16"
                    ></div>
                  ))}
                </div>
              ) : (
                optimizationData && (
                  <div className="flex space-x-4">
                    <div className="text-center px-4 py-3 bg-green-900/30 border border-green-700 rounded-lg">
                      <div className="text-2xl font-bold text-green-400">
                        {optimizationData.optimization_info.success_rate}
                      </div>
                      <div className="text-xs text-green-300">Success Rate</div>
                    </div>
                    <div className="text-center px-4 py-3 bg-blue-900/30 border border-blue-700 rounded-lg">
                      <div className="text-2xl font-bold text-blue-400">
                        {optimizationData.summary_stats.best_return}
                      </div>
                      <div className="text-xs text-blue-300">Best Return</div>
                    </div>
                    <div className="text-center px-4 py-3 bg-purple-900/30 border border-purple-700 rounded-lg">
                      <div className="text-lg font-bold text-purple-400">JPY</div>
                      <div className="text-xs text-purple-300">Dominance</div>
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
          <nav className="flex space-x-8">
            {[
              {
                id: 'overview',
                label: 'Performance Overview',
                icon: '📊',
                disabled: isLoading,
                description: 'Key metrics and results',
              },
              {
                id: 'analytics',
                label: 'Visual Analytics',
                icon: '📈',
                disabled: false,
                description: 'Charts and data visualization',
              },
              {
                id: 'currencies',
                label: 'Currency Analysis',
                icon: '💱',
                disabled: false,
                description: 'Pair-by-pair breakdown',
              },
              {
                id: 'methodology',
                label: 'Strategy Details',
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
                  group py-4 px-1 border-b-2 font-medium text-sm transition-all duration-200
                  ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-400'
                      : tab.disabled
                      ? 'border-transparent text-neutral-600 cursor-not-allowed'
                      : 'border-transparent text-neutral-400 hover:text-neutral-300 hover:border-neutral-600'
                  }
                `}
              >
                <div className="flex items-center space-x-2">
                  <span>{tab.icon}</span>
                  <span>{tab.label}</span>
                </div>
                <div className="text-xs text-neutral-500 group-hover:text-neutral-400 mt-1">
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
          <OverviewTab optimizationData={optimizationData} isLoading={isLoading} />
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
  optimizationData?: OptimizationResults;
  isLoading: boolean;
}

function OverviewTab({ optimizationData, isLoading }: OverviewTabProps) {
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
      {/* Strategy Overview Hero */}
      <div className=" border border-neutral-700 rounded-xl p-8">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-white mb-3">Strategy Performance Summary</h2>
            <p className="text-neutral-300 mb-4 max-w-3xl">
              Comprehensive optimization results for the Enhanced Daily EMA Strategy across{' '}
              {optimizationData.optimization_info.total_pairs_tested} major currency pairs. Our
              systematic approach identified{' '}
              {optimizationData.optimization_info.profitable_pairs_count} consistently profitable
              pairs with a realistic {optimizationData.optimization_info.success_rate} success rate.
            </p>
            <div className="flex items-center space-x-6 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-neutral-400">
                  Profitable Pairs: {Object.keys(optimizationData.profitable_pairs).length}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                <span className="text-neutral-400">
                  Unprofitable Pairs: {Object.keys(optimizationData.unprofitable_pairs).length}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span className="text-neutral-400">
                  {optimizationData.summary_stats.jpy_dominance}
                </span>
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-green-400 mb-1">
              {optimizationData.summary_stats.best_return}
            </div>
            <div className="text-sm text-neutral-400">Peak Annual Return</div>
            <div className="text-lg font-semibold text-blue-400 mt-2">
              {optimizationData.summary_stats.top_performer}
            </div>
            <div className="text-xs text-neutral-500">Top Performing Pair</div>
          </div>
        </div>
      </div>

      {/* Enhanced Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          icon="🎯"
          title="Strategy Success Rate"
          value={optimizationData.optimization_info.success_rate}
          subtitle={`${optimizationData.optimization_info.profitable_pairs_count} of ${optimizationData.optimization_info.total_pairs_tested} pairs profitable`}
          color="green"
          trend="neutral"
        />

        <MetricCard
          icon="🥇"
          title="Best Performance"
          value={optimizationData.summary_stats.best_return}
          subtitle={`${optimizationData.summary_stats.top_performer} leading`}
          color="blue"
          trend="up"
        />

        <MetricCard
          icon="🎌"
          title="JPY Advantage"
          value="4/5"
          subtitle="JPY pairs dominate profitable results"
          color="purple"
          trend="up"
        />

        <MetricCard
          icon="⚡"
          title="Top Win Rate"
          value={optimizationData.summary_stats.best_win_rate}
          subtitle="Achieved by top performers"
          color="yellow"
          trend="up"
        />
      </div>

      {/* Performance Breakdown Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Profitable Pairs */}
        <div className="lg:col-span-2">
          <ProfitablePairsSection profitable_pairs={optimizationData.profitable_pairs} />
        </div>

        {/* Unprofitable Pairs */}
        <div>
          <UnprofitablePairsSection unprofitable_pairs={optimizationData.unprofitable_pairs} />
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
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
  profitable_pairs: OptimizationResults['profitable_pairs'];
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

              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <div className="text-neutral-400">Win Rate</div>
                  <div className="font-semibold">{data.win_rate}</div>
                </div>
                <div>
                  <div className="text-neutral-400">EMA Config</div>
                  <div className="font-semibold">{data.ema_config}</div>
                </div>
                <div>
                  <div className="text-neutral-400">Trades/Year</div>
                  <div className="font-semibold">{data.trades_per_year}</div>
                </div>
              </div>

              {/* Trading Costs Breakdown */}
              <div className="mt-3 pt-3 border-t border-neutral-600">
                <div className="flex justify-between text-xs">
                  <span className="text-neutral-400">
                    Gross Return: <span className="text-green-400">{data.gross_return}%</span>
                  </span>
                  <span className="text-neutral-400">
                    Trading Costs: <span className="text-red-400">-{data.trading_costs}%</span>
                  </span>
                  <span className="text-neutral-400">
                    Net Return: <span className="text-blue-400">{data.net_return}%</span>
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
  unprofitable_pairs: OptimizationResults['unprofitable_pairs'];
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

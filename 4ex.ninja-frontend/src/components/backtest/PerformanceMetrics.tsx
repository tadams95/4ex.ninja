'use client';

import { useQuery } from '@tanstack/react-query';
import {
  getConfidenceAnalysis,
  loadEnhancedOptimizationResults,
  simulateApiDelay,
  type ConfidenceAnalysis,
  type EnhancedOptimizationResults,
} from '../../lib/secondBacktestDataLoader';

/**
 * ENHANCED Performance Metrics Component v2.0
 *
 * Displays comprehensive performance metrics from SECOND BACKTEST RUN
 * Features: 4,436 actual trades across 10 pairs, ALL PROFITABLE
 * Data Source: Enhanced Daily Strategy v2.0 - August 21, 2025
 */
export default function PerformanceMetrics() {
  const {
    data: optimizationData,
    isLoading: isLoadingOptimization,
    error: optimizationError,
  } = useQuery<EnhancedOptimizationResults>({
    queryKey: ['enhanced-optimization-results-v2'],
    queryFn: async () => {
      console.log('Loading ENHANCED optimization results v2.0');
      await simulateApiDelay();
      return loadEnhancedOptimizationResults();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const {
    data: confidenceData,
    isLoading: isLoadingConfidence,
    error: confidenceError,
  } = useQuery<ConfidenceAnalysis | null>({
    queryKey: ['confidence-analysis-v2'],
    queryFn: async () => {
      console.log('Loading confidence analysis v2.0');
      await simulateApiDelay();
      return getConfidenceAnalysis();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const isLoading = isLoadingOptimization || isLoadingConfidence;
  const error = optimizationError || confidenceError;

  if (isLoading) {
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-neutral-700 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-20 bg-neutral-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-700 rounded-lg p-6">
        <p className="text-red-400">Error loading optimization data: {error.message}</p>
      </div>
    );
  }

  if (!optimizationData) {
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <p className="text-neutral-400">No optimization data available</p>
      </div>
    );
  }

  // Calculate aggregate metrics from all profitable pairs (ALL 10 PAIRS are profitable in v2!)
  const profitablePairs = Object.entries(optimizationData.profitable_pairs);
  const totalProfitablePairs = profitablePairs.length;
  const totalTestedPairs = optimizationData.optimization_info.total_pairs_tested;
  const totalTrades = optimizationData.optimization_info.total_trades;

  // Calculate averages across all profitable pairs
  const avgReturn =
    profitablePairs.reduce(
      (sum, [_, pair]) => sum + parseFloat(pair.annual_return.replace('%', '')),
      0
    ) / totalProfitablePairs;

  const avgWinRate =
    profitablePairs.reduce(
      (sum, [_, pair]) => sum + parseFloat(pair.win_rate.replace('%', '')),
      0
    ) / totalProfitablePairs;

  const avgProfitFactor =
    profitablePairs.reduce((sum, [_, pair]) => sum + pair.profit_factor, 0) / totalProfitablePairs;

  const totalPips = profitablePairs.reduce((sum, [_, pair]) => sum + pair.total_pips, 0);

  // Get tier breakdown
  const goldTier = profitablePairs.filter(([_, pair]) => pair.tier === 'GOLD_TIER');
  const silverTier = profitablePairs.filter(([_, pair]) => pair.tier === 'SILVER_TIER');
  const bronzeTier = profitablePairs.filter(([_, pair]) => pair.tier === 'BRONZE_TIER');

  // Find top performer
  const topPerformer = profitablePairs.reduce((top, [pair, data]) => {
    const currentReturn = parseFloat(data.annual_return.replace('%', ''));
    const topReturn = parseFloat(top[1].annual_return.replace('%', ''));
    return currentReturn > topReturn ? [pair, data] : top;
  });

  const performanceMetrics = [
    {
      label: 'Success Rate',
      value: `${Math.round((totalProfitablePairs / totalTestedPairs) * 100)}%`,
      description: `ALL ${totalProfitablePairs} pairs profitable!`,
      color: 'text-green-400',
    },
    {
      label: 'Total Trades',
      value: totalTrades.toLocaleString(),
      description: 'Actual backtest trades executed',
      color: 'text-purple-400',
    },
    {
      label: 'Top Performer',
      value: topPerformer[0],
      description: `${topPerformer[1].annual_return} annual return`,
      color: 'text-yellow-400',
    },
    {
      label: 'Avg Return',
      value: `${avgReturn.toFixed(1)}%`,
      description: 'Average across all pairs',
      color:
        avgReturn >= 10 ? 'text-green-400' : avgReturn >= 8 ? 'text-yellow-400' : 'text-orange-400',
    },
    {
      label: 'Avg Win Rate',
      value: `${avgWinRate.toFixed(1)}%`,
      description: 'Average across all pairs',
      color:
        avgWinRate >= 50 ? 'text-green-400' : avgWinRate >= 40 ? 'text-yellow-400' : 'text-red-400',
    },
    {
      label: 'Avg Profit Factor',
      value: `${avgProfitFactor.toFixed(2)}x`,
      description: 'Average profitability ratio',
      color:
        avgProfitFactor >= 1.5
          ? 'text-green-400'
          : avgProfitFactor >= 1.2
          ? 'text-yellow-400'
          : 'text-orange-400',
    },
    {
      label: 'Total Pips',
      value: Math.round(totalPips).toLocaleString(),
      description: 'Combined profit across all pairs',
      color: 'text-blue-400',
    },
    {
      label: 'Gold Tier Pairs',
      value: goldTier.length.toString(),
      description: 'Highest performance tier',
      color: goldTier.length >= 3 ? 'text-yellow-400' : 'text-orange-400',
    },
    {
      label: 'Strategy Version',
      value: 'v2.0',
      description: 'Enhanced Daily Strategy',
      color: 'text-cyan-400',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header with Enhanced Results Overview */}
      <div className="bg-gradient-to-r from-green-900/30 to-blue-900/30 border border-green-700/50 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-2">
          🚀 Performance Metrics - Enhanced Results v2.0
        </h2>
        <p className="text-green-400 font-medium mb-2">
          🎯 BREAKTHROUGH: ALL {totalProfitablePairs} pairs profitable!{' '}
          {totalTrades.toLocaleString()} total trades
        </p>
        <p className="text-neutral-300 text-sm">{optimizationData.optimization_info.methodology}</p>

        {/* Confidence Disclaimer */}
        {confidenceData && (
          <div className="mt-4 p-3 bg-yellow-900/20 border border-yellow-700 rounded-lg">
            <p className="text-yellow-400 text-sm font-medium">
              ⚠️ Confidence Analysis: {confidenceData.reality_adjustments.realistic_expectation}
            </p>
          </div>
        )}
      </div>

      {/* Performance Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {performanceMetrics.map((metric, index) => (
          <div
            key={index}
            className="bg-neutral-800 border border-neutral-700 rounded-lg p-4 hover:border-neutral-600 transition-colors"
          >
            <div className="flex flex-col">
              <span className="text-neutral-400 text-sm font-medium mb-1">{metric.label}</span>
              <span className={`text-2xl font-bold mb-1 ${metric.color}`}>{metric.value}</span>
              <span className="text-neutral-500 text-xs">{metric.description}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Enhanced Profitable Pairs Analysis */}
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">
          Enhanced Profitable Pairs Analysis
        </h3>
        <div className="mb-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-3 bg-yellow-900/20 border border-yellow-700 rounded-lg">
            <div className="text-yellow-400 font-bold text-lg">🥇 {goldTier.length}</div>
            <div className="text-xs text-yellow-300">Gold Tier</div>
          </div>
          <div className="text-center p-3 bg-gray-700/20 border border-gray-600 rounded-lg">
            <div className="text-gray-300 font-bold text-lg">🥈 {silverTier.length}</div>
            <div className="text-xs text-gray-400">Silver Tier</div>
          </div>
          <div className="text-center p-3 bg-orange-900/20 border border-orange-700 rounded-lg">
            <div className="text-orange-400 font-bold text-lg">🥉 {bronzeTier.length}</div>
            <div className="text-xs text-orange-300">Bronze Tier</div>
          </div>
        </div>

        <div className="space-y-3">
          {profitablePairs.map(([pair, data]) => {
            const tierColor =
              data.tier === 'GOLD_TIER'
                ? 'text-yellow-400'
                : data.tier === 'SILVER_TIER'
                ? 'text-gray-300'
                : 'text-orange-400';
            const isJPY = pair.includes('JPY');

            return (
              <div
                key={pair}
                className="flex items-center justify-between p-3 bg-neutral-900/50 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{data.tier_icon}</span>
                  <div>
                    <span className="text-white font-medium">{pair}</span>
                    {isJPY && (
                      <span className="ml-2 bg-yellow-400 text-black px-2 py-1 rounded text-xs font-bold">
                        JPY
                      </span>
                    )}
                    <p className={`text-sm ${tierColor}`}>{data.tier.replace('_', ' ')}</p>
                  </div>
                </div>
                <div className="grid grid-cols-4 gap-4 text-center">
                  <div>
                    <div className="text-green-400 font-bold">{data.annual_return}</div>
                    <div className="text-xs text-neutral-400">Return</div>
                  </div>
                  <div>
                    <div className="text-blue-400 font-bold">{data.win_rate}</div>
                    <div className="text-xs text-neutral-400">Win Rate</div>
                  </div>
                  <div>
                    <div className="text-purple-400 font-bold">
                      {data.profit_factor.toFixed(2)}x
                    </div>
                    <div className="text-xs text-neutral-400">Profit Factor</div>
                  </div>
                  <div>
                    <div className="text-cyan-400 font-bold">{data.total_trades}</div>
                    <div className="text-xs text-neutral-400">Total Trades</div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Enhanced Strategy Insights */}
      <div className="bg-gradient-to-r from-green-900/20 to-blue-900/20 border border-green-600/50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-green-400 mb-3">
          🎉 Enhanced Strategy v2.0 - Major Breakthrough
        </h3>
        <div className="mb-4">
          <p className="text-neutral-300 text-sm mb-2">
            Significant improvements achieved through strategy enhancement:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div className="text-green-400">
                ✅ ALL {totalProfitablePairs} pairs profitable (100% success rate)
              </div>
              <div className="text-green-400">
                ✅ {totalTrades.toLocaleString()} total trades executed
              </div>
              <div className="text-green-400">
                ✅ {avgProfitFactor.toFixed(2)}x average profit factor
              </div>
            </div>
            <div className="space-y-2">
              <div className="text-blue-400">📊 {goldTier.length} Gold tier performers</div>
              <div className="text-blue-400">
                📊 {Math.round(totalPips).toLocaleString()} total pips gained
              </div>
              <div className="text-blue-400">📊 {avgReturn.toFixed(1)}% average annual return</div>
            </div>
          </div>
        </div>
        <div className="pt-4 border-t border-neutral-700">
          <h4 className="text-white font-medium mb-2">Key Strategy Enhancements:</h4>
          <ul className="text-neutral-300 text-sm space-y-1">
            <li>✅ Enhanced moving average calculations with dynamic periods</li>
            <li>✅ Improved signal validation and entry timing</li>
            <li>✅ Optimized risk management parameters</li>
            <li>✅ Comprehensive backtesting across full dataset</li>
          </ul>
        </div>
      </div>

      {/* Top Performers Spotlight */}
      <div className="bg-gradient-to-r from-yellow-900/20 to-green-900/20 border border-yellow-600/50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-yellow-400 mb-3">
          � Top Performers - Enhanced Results
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {goldTier.slice(0, 2).map(([pair, data]) => (
            <div key={pair}>
              <h4 className="text-white font-medium mb-2 flex items-center space-x-2">
                <span>{data.tier_icon}</span>
                <span>{pair} (Gold Tier)</span>
              </h4>
              <ul className="text-green-400 text-sm space-y-1">
                <li>🥇 {data.annual_return} annual return</li>
                <li>🎯 {data.win_rate} win rate</li>
                <li>💪 {data.profit_factor.toFixed(2)}x profit factor</li>
                <li>📊 {data.total_trades} trades executed</li>
                <li>💰 {Math.round(data.total_pips).toLocaleString()} pips gained</li>
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

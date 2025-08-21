'use client';

import { useQuery } from '@tanstack/react-query';
import {
  loadOptimizationResults,
  simulateApiDelay,
  type OptimizationResults,
} from '../../lib/realOptimizationDataLoader';

/**
 * VERIFIED Performance Metrics Component
 *
 * Displays comprehensive performance metrics from REAL optimization results
 * Features the actual results: only 2 pairs are highly profitable (USD_JPY, EUR_JPY)
 */
export default function PerformanceMetrics() {
  const {
    data: optimizationData,
    isLoading,
    error,
  } = useQuery<OptimizationResults>({
    queryKey: ['verified-optimization-results'],
    queryFn: async () => {
      console.log('Loading VERIFIED optimization results');
      await simulateApiDelay();
      return loadOptimizationResults();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

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

  // Calculate aggregate metrics from profitable pairs
  const profitablePairs = Object.entries(optimizationData.profitable_pairs);
  const totalProfitablePairs = profitablePairs.length;
  const totalTestedPairs = optimizationData.optimization_info.total_pairs_tested;

  // Calculate averages for profitable pairs only
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
  const totalTrades = profitablePairs.reduce((sum, [_, pair]) => sum + pair.trades_per_year, 0);

  // Get top performers (highly profitable)
  const highlyProfitable = profitablePairs.filter(([_, pair]) => pair.tier === 'HIGHLY_PROFITABLE');

  const performanceMetrics = [
    {
      label: 'Success Rate',
      value: `${Math.round((totalProfitablePairs / totalTestedPairs) * 100)}%`,
      description: `${totalProfitablePairs} out of ${totalTestedPairs} pairs profitable`,
      color: totalProfitablePairs >= 5 ? 'text-green-400' : 'text-yellow-400',
    },
    {
      label: 'Top Performer',
      value: optimizationData.summary_stats.top_performer,
      description: `${optimizationData.summary_stats.best_return} annual return`,
      color: 'text-green-400',
    },
    {
      label: 'Best Win Rate',
      value: optimizationData.summary_stats.best_win_rate,
      description: 'Achieved by top JPY pairs',
      color: 'text-blue-400',
    },
    {
      label: 'Avg Profitable Return',
      value: `${avgReturn.toFixed(1)}%`,
      description: 'Average across profitable pairs',
      color:
        avgReturn >= 10 ? 'text-green-400' : avgReturn >= 5 ? 'text-yellow-400' : 'text-orange-400',
    },
    {
      label: 'Avg Win Rate',
      value: `${avgWinRate.toFixed(1)}%`,
      description: 'Average across profitable pairs',
      color:
        avgWinRate >= 60 ? 'text-green-400' : avgWinRate >= 45 ? 'text-yellow-400' : 'text-red-400',
    },
    {
      label: 'Total Annual Trades',
      value: totalTrades.toString(),
      description: 'Combined across all strategies',
      color: 'text-purple-400',
    },
    {
      label: 'Highly Profitable Pairs',
      value: highlyProfitable.length.toString(),
      description: 'Above 10% annual return',
      color: highlyProfitable.length >= 2 ? 'text-green-400' : 'text-yellow-400',
    },
    {
      label: 'JPY Dominance',
      value: '80%',
      description: '4 out of 5 profitable pairs',
      color: 'text-yellow-400',
    },
    {
      label: 'Methodology',
      value: 'Realistic',
      description: '1.5% SL, 3% TP, trading costs',
      color: 'text-blue-400',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header with Real Results Reality Check */}
      <div className="bg-gradient-to-r from-orange-900/30 to-yellow-900/30 border border-orange-700/50 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-2">
          ✅ VERIFIED Performance Metrics - REAL Results
        </h2>
        <p className="text-orange-400 font-medium mb-2">
          🎯 REALITY: Only 2 pairs are highly profitable (USD_JPY: 14%, EUR_JPY: 13.5%)
        </p>
        <p className="text-neutral-300 text-sm">{optimizationData.optimization_info.methodology}</p>
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

      {/* Detailed Profitable Pairs Analysis */}
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">
          Profitable Pairs Breakdown (REAL Data)
        </h3>
        <div className="space-y-3">
          {profitablePairs.map(([pair, data]) => {
            const tierColor =
              data.tier === 'HIGHLY_PROFITABLE'
                ? 'text-green-400'
                : data.tier === 'PROFITABLE'
                ? 'text-yellow-400'
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
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-green-400 font-bold">{data.annual_return}</div>
                    <div className="text-xs text-neutral-400">Return</div>
                  </div>
                  <div>
                    <div className="text-blue-400 font-bold">{data.win_rate}</div>
                    <div className="text-xs text-neutral-400">Win Rate</div>
                  </div>
                  <div>
                    <div className="text-purple-400 font-bold">{data.trades_per_year}</div>
                    <div className="text-xs text-neutral-400">Trades/Yr</div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Reality Check Section */}
      <div className="bg-gradient-to-r from-red-900/20 to-orange-900/20 border border-red-600/50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-red-400 mb-3">
          🚨 Reality Check - Unprofitable Pairs
        </h3>
        <div className="mb-4">
          <p className="text-neutral-300 text-sm mb-2">
            5 out of 10 pairs tested were unprofitable after realistic trading costs:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
            {Object.entries(optimizationData.unprofitable_pairs).map(([pair, data]) => (
              <div key={pair} className="text-red-400">
                • {pair}: {data.annual_return} ({data.win_rate} win rate)
              </div>
            ))}
          </div>
        </div>
        <div className="pt-4 border-t border-neutral-700">
          <h4 className="text-white font-medium mb-2">Key Learnings:</h4>
          <ul className="text-neutral-300 text-sm space-y-1">
            <li>✅ Only 2 pairs achieve strong double-digit returns</li>
            <li>✅ JPY pairs dominate profitable strategies (80%)</li>
            <li>✅ Realistic trading costs significantly impact results</li>
            <li>✅ Conservative approach: Focus on top 2-3 performers</li>
          </ul>
        </div>
      </div>

      {/* JPY Strategy Focus */}
      <div className="bg-gradient-to-r from-yellow-900/20 to-green-900/20 border border-yellow-600/50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-yellow-400 mb-3">
          🎌 JPY Strategy Focus - The Real Winners
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-white font-medium mb-2">USD_JPY (Gold Tier):</h4>
            <ul className="text-green-400 text-sm space-y-1">
              <li>🥇 14.0% annual return</li>
              <li>🎯 70% win rate</li>
              <li>⚡ 20/60 EMA configuration</li>
              <li>📊 10 trades per year</li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-medium mb-2">EUR_JPY (Gold Tier):</h4>
            <ul className="text-green-400 text-sm space-y-1">
              <li>🥇 13.5% annual return</li>
              <li>🎯 70% win rate</li>
              <li>⚡ 30/60 EMA configuration</li>
              <li>📊 10 trades per year</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

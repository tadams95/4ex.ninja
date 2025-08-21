'use client';

import { useQuery } from '@tanstack/react-query';
import {
  getCurrencyAnalysis,
  simulateApiDelay,
  type CurrencyData,
} from '../../lib/realOptimizationDataLoader';

/**
 * Enhanced Daily EMA Strategy - Currency Analysis Component
 *
 * Displays detailed analysis of profitable currency pairs from our comprehensive
 * 10-pair optimization study using the Enhanced Daily EMA Strategy.
 * Shows real performance data with JPY dominance insights.
 */
export default function CurrencyAnalysis() {
  const {
    data: currencyData,
    isLoading,
    error,
  } = useQuery<CurrencyData[]>({
    queryKey: ['enhanced-daily-ema-currency-analysis'],
    queryFn: async () => {
      console.log(
        'Loading Enhanced Daily EMA Strategy currency analysis from optimization results'
      );
      await simulateApiDelay();
      return getCurrencyAnalysis();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  if (isLoading) {
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-neutral-700 rounded w-1/3"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-32 bg-neutral-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-700 rounded-lg p-6">
        <p className="text-red-400">Error loading currency analysis: {error.message}</p>
      </div>
    );
  }

  if (!currencyData || currencyData.length === 0) {
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <p className="text-neutral-400">No currency analysis data available</p>
      </div>
    );
  }

  // Helper function to get tier-based styling
  const getTierStyling = (tier: string) => {
    switch (tier.toUpperCase()) {
      case 'HIGHLY_PROFITABLE':
        return {
          border: 'border-emerald-400',
          bg: 'bg-gradient-to-r from-emerald-900/20 to-emerald-800/20',
          text: 'text-emerald-400',
          icon: '🥇',
          label: 'Highly Profitable',
        };
      case 'PROFITABLE':
        return {
          border: 'border-blue-400',
          bg: 'bg-gradient-to-r from-blue-900/20 to-blue-800/20',
          text: 'text-blue-400',
          icon: '🥈',
          label: 'Profitable',
        };
      case 'MARGINALLY_PROFITABLE':
        return {
          border: 'border-amber-400',
          bg: 'bg-gradient-to-r from-amber-900/20 to-amber-800/20',
          text: 'text-amber-400',
          icon: '🥉',
          label: 'Marginally Profitable',
        };
      default:
        return {
          border: 'border-neutral-600',
          bg: 'bg-neutral-800/50',
          text: 'text-neutral-300',
          icon: '⭐',
          label: 'Profitable',
        };
    }
  };

  // Get JPY and non-JPY pairs
  const jpyPairs = currencyData.filter(pair => pair.pair.includes('JPY'));
  const nonJpyPairs = currencyData.filter(pair => !pair.pair.includes('JPY'));

  return (
    <div className="space-y-6">
      {/* Header with Strategy Introduction */}
      <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 border border-blue-700/50 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-3">
          📊 Enhanced Daily EMA Strategy - Currency Analysis
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <h3 className="text-emerald-400 font-medium mb-2">Strategy Overview</h3>
            <ul className="text-neutral-300 text-sm space-y-1">
              <li>• Daily timeframe EMA crossover system</li>
              <li>• Pair-specific optimization (EMA 20/60 vs 30/60)</li>
              <li>• Enhanced with session filtering & confluence</li>
              <li>• Fixed 1.5% SL, 3.0% TP (2:1 risk-reward)</li>
            </ul>
          </div>
          <div>
            <h3 className="text-blue-400 font-medium mb-2">Optimization Results</h3>
            <ul className="text-neutral-300 text-sm space-y-1">
              <li>• 10 major forex pairs tested</li>
              <li>• 50% success rate (5 profitable pairs)</li>
              <li>• Realistic trading cost modeling</li>
              <li>• {jpyPairs.length}/5 profitable pairs are JPY-based</li>
            </ul>
          </div>
        </div>
        <div className="bg-emerald-900/20 border border-emerald-700/50 rounded-lg p-4">
          <p className="text-emerald-400 font-medium mb-1">🎯 Key Discovery:</p>
          <p className="text-neutral-300 text-sm">
            JPY pairs demonstrate superior trend-following characteristics, achieving
            {jpyPairs.length > 0
              ? ` consistent win rates of ${Math.round(
                  jpyPairs.reduce((sum, p) => sum + p.win_rate, 0) / jpyPairs.length
                )}%`
              : ' strong performance'}
            compared to traditional major pairs like EUR_USD (-4.6%) and GBP_USD (-3.0%).
          </p>
        </div>
      </div>

      {/* JPY Pairs Section */}
      {jpyPairs.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center space-x-3">
            <h3 className="text-lg font-semibold text-emerald-400">🎌 JPY Pairs Performance</h3>
            <span className="bg-emerald-500 text-black px-3 py-1 rounded-full text-xs font-bold">
              {jpyPairs.length} PAIRS PROFITABLE
            </span>
            <span className="bg-blue-600 text-white px-3 py-1 rounded-full text-xs">
              Enhanced Daily EMA Optimized
            </span>
          </div>

          <div className="grid gap-4">
            {jpyPairs.map((currency, index) => {
              const styling = getTierStyling(currency.tier);
              const isTopPerformer = index === 0;

              return (
                <div
                  key={currency.pair}
                  className={`${styling.bg} border ${
                    styling.border
                  } rounded-lg p-6 hover:border-opacity-80 transition-all duration-200 ${
                    isTopPerformer ? 'ring-2 ring-green-500/50' : ''
                  }`}
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between">
                    <div className="flex items-center space-x-3 mb-4 md:mb-0">
                      <div className="text-3xl">{currency.tier_icon || styling.icon}</div>
                      <div>
                        <h4 className="text-xl font-bold text-white">
                          {currency.pair}
                          {isTopPerformer && (
                            <span className="ml-2 bg-emerald-500 text-black px-2 py-1 rounded text-xs font-bold">
                              STRATEGY LEADER
                            </span>
                          )}
                        </h4>
                        <p className={`text-sm font-medium ${styling.text}`}>
                          {styling.label} • EMA {currency.ema_config}
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-6">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-400">
                          {currency.annual_return.toFixed(1)}%
                        </div>
                        <div className="text-xs text-neutral-400">Annual Return</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-400">
                          {currency.win_rate.toFixed(0)}%
                        </div>
                        <div className="text-xs text-neutral-400">Win Rate</div>
                      </div>
                      <div className="text-center md:col-span-1 col-span-2">
                        <div className="text-2xl font-bold text-purple-400">
                          {currency.trades_per_year}
                        </div>
                        <div className="text-xs text-neutral-400">Trades/Year</div>
                      </div>
                    </div>
                  </div>

                  {/* Strategy-specific insights */}
                  <div className="mt-4 pt-4 border-t border-neutral-700">
                    <h5 className="text-white font-medium mb-2">
                      Enhanced Daily EMA Strategy - JPY Advantages:
                    </h5>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                      <div className="flex items-center space-x-2">
                        <span className="text-emerald-400">✓</span>
                        <span className="text-neutral-300">Optimal EMA crossover response</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-emerald-400">✓</span>
                        <span className="text-neutral-300">Strong daily timeframe trends</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-emerald-400">✓</span>
                        <span className="text-neutral-300">Low noise-to-signal ratio</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-emerald-400">✓</span>
                        <span className="text-neutral-300">
                          Consistent 2:1 risk-reward achievement
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Non-JPY Pairs Section */}
      {nonJpyPairs.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center space-x-3">
            <h3 className="text-lg font-semibold text-blue-400">🌟 Non-JPY Profitable Pairs</h3>
            <span className="bg-blue-500 text-white px-3 py-1 rounded-full text-xs font-bold">
              {nonJpyPairs.length} PAIR PROFITABLE
            </span>
            <span className="bg-amber-600 text-white px-3 py-1 rounded-full text-xs">
              Exception Performance
            </span>
          </div>

          <div className="grid gap-4">
            {nonJpyPairs.map((currency, index) => {
              const styling = getTierStyling(currency.tier);

              return (
                <div
                  key={currency.pair}
                  className={`${styling.bg} border ${styling.border} rounded-lg p-6 hover:border-opacity-80 transition-all duration-200`}
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between">
                    <div className="flex items-center space-x-3 mb-4 md:mb-0">
                      <div className="text-3xl">{currency.tier_icon || styling.icon}</div>
                      <div>
                        <h4 className="text-xl font-bold text-white">
                          {currency.pair}
                          <span className="ml-2 bg-blue-500 text-white px-2 py-1 rounded text-xs font-bold">
                            NON-JPY SUCCESS
                          </span>
                        </h4>
                        <p className={`text-sm font-medium ${styling.text}`}>
                          {styling.label} • EMA {currency.ema_config}
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-6">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-400">
                          {currency.annual_return.toFixed(1)}%
                        </div>
                        <div className="text-xs text-neutral-400">Annual Return</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-400">
                          {currency.win_rate.toFixed(0)}%
                        </div>
                        <div className="text-xs text-neutral-400">Win Rate</div>
                      </div>
                      <div className="text-center md:col-span-1 col-span-2">
                        <div className="text-2xl font-bold text-purple-400">
                          {currency.trades_per_year}
                        </div>
                        <div className="text-xs text-neutral-400">Trades/Year</div>
                      </div>
                    </div>
                  </div>

                  {/* Non-JPY strategy insights */}
                  <div className="mt-4 pt-4 border-t border-neutral-700">
                    <h5 className="text-white font-medium mb-2">
                      Why This Non-JPY Pair Succeeds with Enhanced Daily EMA:
                    </h5>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                      <div className="flex items-center space-x-2">
                        <span className="text-blue-400">✓</span>
                        <span className="text-neutral-300">Strong EMA parameter response</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-blue-400">✓</span>
                        <span className="text-neutral-300">Optimal London/NY session behavior</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-blue-400">✓</span>
                        <span className="text-neutral-300">Overcomes trading cost hurdle</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-blue-400">✓</span>
                        <span className="text-neutral-300">
                          Consistent trend-following behavior
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Strategy Performance Summary */}
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">
          Enhanced Daily EMA Strategy - Performance Summary
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="text-center">
            <h4 className="text-emerald-400 font-medium mb-2">✅ Strategy Success Rate</h4>
            <p className="text-2xl font-bold text-white mb-1">
              {Math.round((currencyData.length / 10) * 100)}%
            </p>
            <p className="text-neutral-400 text-sm">{currencyData.length} of 10 pairs profitable</p>
          </div>

          <div className="text-center">
            <h4 className="text-blue-400 font-medium mb-2">📈 Average Return</h4>
            <p className="text-2xl font-bold text-white mb-1">
              {(
                currencyData.reduce((sum, curr) => sum + curr.annual_return, 0) /
                currencyData.length
              ).toFixed(1)}
              %
            </p>
            <p className="text-neutral-400 text-sm">Profitable pairs average</p>
          </div>

          <div className="text-center">
            <h4 className="text-purple-400 font-medium mb-2">🎯 Average Win Rate</h4>
            <p className="text-2xl font-bold text-white mb-1">
              {Math.round(
                currencyData.reduce((sum, curr) => sum + curr.win_rate, 0) / currencyData.length
              )}
              %
            </p>
            <p className="text-neutral-400 text-sm">Across profitable pairs</p>
          </div>

          <div className="text-center">
            <h4 className="text-yellow-400 font-medium mb-2">🎌 JPY Dominance</h4>
            <p className="text-2xl font-bold text-white mb-1">
              {Math.round((jpyPairs.length / currencyData.length) * 100)}%
            </p>
            <p className="text-neutral-400 text-sm">JPY pairs in profitable set</p>
          </div>
        </div>

        {/* Strategy Insights */}
        <div className="mt-6 pt-6 border-t border-neutral-700">
          <h4 className="text-white font-medium mb-3">Enhanced Daily EMA Strategy Key Insights:</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h5 className="text-emerald-400 font-medium mb-2">✅ What Works</h5>
              <ul className="text-neutral-300 text-sm space-y-1">
                <li>• JPY pairs show superior EMA crossover reliability</li>
                <li>• Daily timeframe provides optimal signal clarity</li>
                <li>• 2:1 risk-reward consistently achievable</li>
                <li>• Session filtering enhances JPY pair performance</li>
              </ul>
            </div>
            <div>
              <h5 className="text-red-400 font-medium mb-2">❌ Strategy Limitations</h5>
              <ul className="text-neutral-300 text-sm space-y-1">
                <li>• EUR_USD (-4.6%) despite high liquidity</li>
                <li>• GBP_USD (-3.0%) too volatile for this approach</li>
                <li>• Cross pairs like EUR_GBP (-4.2%) struggle</li>
                <li>• Trading costs significantly impact lower performers</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Implementation Note */}
        <div className="mt-6 pt-6 border-t border-neutral-700">
          <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-4">
            <h5 className="text-blue-400 font-medium mb-2">📋 Implementation Strategy</h5>
            <p className="text-neutral-300 text-sm">
              Based on these results, the Enhanced Daily EMA Strategy recommends prioritizing JPY
              pairs (USD_JPY, EUR_JPY) for primary allocation, with careful position sizing and
              realistic performance expectations. The strategy's strength lies in its systematic
              approach to trend-following with proper risk management rather than high-frequency
              trading.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

'use client';

import dynamic from 'next/dynamic';

// Dynamic import to ensure client-side only rendering (following your pattern)
const DynamicBacktestDashboard = dynamic(
  () =>
    import('../../components/backtest/BacktestDashboard').then(mod => ({ default: mod.default })),
  {
    ssr: false,
    loading: () => (
      <div className="min-h-screen bg-black text-white">
        <div className="border-b border-neutral-700 bg-black">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div>
                <h1 className="text-2xl font-bold text-white">🎯 VERIFIED Optimization Results</h1>
                <p className="text-sm text-neutral-400">
                  Real 10-pair Enhanced Daily Strategy • JPY Dominance Confirmed • Aug 2025
                </p>
              </div>
              <div className="flex items-center space-x-4">
                <div className="px-3 py-2 text-sm bg-neutral-600 rounded-md animate-pulse">
                  Loading...
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <div
                key={i}
                className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-lg h-48"
              />
            ))}
          </div>
        </div>
      </div>
    ),
  }
);

/**
 * Backtest Results Page
 *
 * Route: /backtest
 * Displays comprehensive backtest performance results for the MA Unified Strategy
 */
export default function BacktestPage() {
  return <DynamicBacktestDashboard />;
}

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
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between py-6 space-y-4 lg:space-y-0">
              <div className="flex-1">
                <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-white">🎯 VERIFIED Optimization Results</h1>
                <p className="text-sm text-neutral-400 mt-1">
                  Real 10-pair Enhanced Daily Strategy • JPY Dominance Confirmed • Aug 2025
                </p>
              </div>
              <div className="flex items-center justify-center lg:justify-end">
                <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                  <div className="px-3 py-2 text-sm bg-neutral-600 rounded-md animate-pulse min-w-[6rem] text-center">
                    Loading...
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
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

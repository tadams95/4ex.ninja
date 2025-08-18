'use client';

import dynamic from 'next/dynamic';

// Dynamic import to ensure client-side only rendering (like regime monitoring)
const DynamicRiskDashboard = dynamic(
  () => import('../../components/dashboard/RiskDashboard').then(mod => ({ default: mod.default })),
  {
    ssr: false,
    loading: () => (
      <div className="min-h-screen bg-black text-white">
        <div className="border-b border-neutral-700 bg-black">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div>
                <h1 className="text-2xl font-bold text-white">Risk Dashboard</h1>
                <p className="text-sm text-neutral-400">
                  Real-time VaR monitoring and correlation analysis
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
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <div className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-lg h-64"></div>
            <div className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-lg h-64"></div>
          </div>
        </div>
      </div>
    ),
  }
);

/**
 * Risk Dashboard Page
 *
 * Route: /risk-dashboard
 * Displays the main risk monitoring dashboard for Phase 2 implementation
 */
export default function RiskDashboardPage() {
  return <DynamicRiskDashboard />;
}

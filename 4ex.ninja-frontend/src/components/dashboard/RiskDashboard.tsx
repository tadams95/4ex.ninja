'use client';

import dynamic from 'next/dynamic';
import { useEffect, useState } from 'react';

// Dynamic imports to ensure client-side only rendering (like regime monitoring)
const VaRDisplay = dynamic(() => import('./VaRDisplay'), {
  ssr: false,
  loading: () => (
    <div className="p-6 bg-white rounded-lg shadow-lg border border-gray-200">
      <div className="animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          <div className="h-4 bg-gray-200 rounded w-4/6"></div>
        </div>
      </div>
    </div>
  ),
});

const CorrelationHeatMap = dynamic(() => import('./CorrelationHeatMap'), {
  ssr: false,
  loading: () => (
    <div className="p-6 bg-white rounded-lg shadow-lg border border-gray-200">
      <div className="animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="grid grid-cols-4 gap-2">
          {Array.from({ length: 16 }).map((_, i) => (
            <div key={i} className="h-12 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    </div>
  ),
});

/**
 * Risk Dashboard Component
 *
 * Main dashboard for Phase 2 VaR and Correlation monitoring
 * Displays real-time portfolio risk metrics and correlation analysis
 */
export default function RiskDashboard() {
  const [lastUpdated, setLastUpdated] = useState<string>('--:--:--');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setLastUpdated(new Date().toLocaleTimeString());

    // Update timestamp every 30 seconds
    const interval = setInterval(() => {
      setLastUpdated(new Date().toLocaleTimeString());
    }, 30000);

    return () => clearInterval(interval);
  }, []);
  return (
    <div className="p-6 space-y-6">
      {/* Dashboard Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Risk Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-300 mt-1">
            Real-time VaR monitoring and correlation analysis
          </p>
        </div>
        <div className="text-sm text-gray-500 dark:text-gray-400">Last updated: {lastUpdated}</div>
      </div>

      {/* Main Dashboard Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* VaR Display Card */}
        <div>
          <VaRDisplay refreshInterval={30000} />
        </div>

        {/* Correlation Heat Map Card */}
        <div>
          <CorrelationHeatMap refreshInterval={30000} />
        </div>
      </div>

      {/* Secondary Grid Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* VaR Trend Placeholder */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            VaR Trend Analysis
          </h3>
          <div className="h-48 bg-gray-100 dark:bg-gray-700 rounded flex items-center justify-center">
            <span className="text-gray-500 dark:text-gray-400">
              Chart placeholder - Coming in Task 2.2
            </span>
          </div>
        </div>

        {/* Alert Panel Placeholder */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Risk Alerts</h3>
          <div className="space-y-3">
            <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded border-l-4 border-green-400">
              <div className="text-sm font-medium text-green-800 dark:text-green-200">
                All Systems Normal
              </div>
              <div className="text-xs text-green-600 dark:text-green-300 mt-1">
                No risk breaches detected
              </div>
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
              Alert system coming in Task 3.x
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

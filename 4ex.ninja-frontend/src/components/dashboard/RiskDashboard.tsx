'use client';

import dynamic from 'next/dynamic';
import { useCallback, useEffect, useState } from 'react';
import { Button } from '../ui/Button';

// Create a ref to communicate with child components
let globalRefetchCallbacks: (() => void)[] = [];

export const registerRefetchCallback = (callback: () => void) => {
  globalRefetchCallbacks.push(callback);
  return () => {
    globalRefetchCallbacks = globalRefetchCallbacks.filter(cb => cb !== callback);
  };
};

// Dynamic imports to ensure client-side only rendering (like regime monitoring)
const VaRDisplay = dynamic(() => import('./VaRDisplay').then(mod => ({ default: mod.default })), {
  ssr: false,
  loading: () => (
    <div className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-lg h-64"></div>
  ),
});

const CorrelationHeatMap = dynamic(
  () => import('./CorrelationHeatMap').then(mod => ({ default: mod.default })),
  {
    ssr: false,
    loading: () => (
      <div className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-lg h-64"></div>
    ),
  }
);

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

  const handleRefresh = useCallback(() => {
    setLastUpdated(new Date().toLocaleTimeString());
    // Trigger refetch in all child components that use useRiskData
    globalRefetchCallbacks.forEach(callback => {
      try {
        callback();
      } catch (error) {
        console.error('Error calling refetch callback:', error);
      }
    });
  }, []);

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
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
              <div className="text-sm text-neutral-400">Last updated: {lastUpdated}</div>
              <Button onClick={handleRefresh} variant="primary" size="sm">
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Live Data Indicator */}
        <div className="mb-8 p-5 bg-neutral-800 rounded-lg border border-neutral-700 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                <span className="text-green-400 font-medium text-sm">Live Risk Data</span>
              </div>
              <div className="text-neutral-400 text-sm">Real-time VaR & Correlation Analysis</div>
            </div>
          </div>
        </div>

        {/* Main Dashboard Grid */}
        <div className="mb-8">
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
        </div>

        {/* Secondary Grid Row */}
        <div className="mb-8">
          <div className="mb-4">
            <h2 className="text-xl font-semibold text-white mb-2">Risk Analytics</h2>
            <p className="text-sm text-neutral-400">Extended risk analysis and monitoring panels</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* VaR Trend Placeholder */}
            <div className="lg:col-span-2 bg-neutral-800 rounded-lg border border-neutral-700 p-6 shadow-lg">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-white mb-2">VaR Trend Analysis</h3>
                <p className="text-sm text-neutral-400">Historical VaR trends and patterns</p>
              </div>
              <div className="h-48 bg-neutral-700 rounded flex items-center justify-center">
                <span className="text-neutral-400">Chart placeholder - Coming in Task 2.2</span>
              </div>
            </div>

            {/* Alert Panel */}
            <div className="bg-neutral-800 rounded-lg border border-neutral-700 p-6 shadow-lg">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-white mb-2">Risk Alerts</h3>
                <p className="text-sm text-neutral-400">Current system status</p>
              </div>
              <div className="space-y-3">
                <div className="p-3 bg-green-900/20 rounded border-l-4 border-green-400">
                  <div className="text-sm font-medium text-green-400">All Systems Normal</div>
                  <div className="text-xs text-green-300 mt-1">No risk breaches detected</div>
                </div>
                <div className="text-xs text-neutral-400 text-center">
                  Alert system coming in Task 3.x
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Status Bar - System Information */}
        <div className="mt-6 p-5 bg-neutral-800 rounded-lg border border-neutral-700 shadow-lg">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-6">
              <div className="flex items-center">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                <span className="text-neutral-400 font-medium">Risk Engine: Active</span>
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
                <span className="text-neutral-400">Last Update: {lastUpdated}</span>
              </div>
            </div>
            <div className="text-neutral-500 font-medium">4ex.ninja Risk Dashboard v2.0</div>
          </div>
        </div>
      </div>
    </div>
  );
}

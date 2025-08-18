import { useEffect, useState } from 'react';
import VaRDisplay from './VaRDisplay';

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
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* VaR Display Card */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Portfolio VaR
          </h3>
          <VaRDisplay refreshInterval={30} />
        </div>

        {/* Correlation Heatmap Card */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Correlation Matrix
          </h3>
          <div className="space-y-4">
            {/* Placeholder content */}
            <div className="grid grid-cols-4 gap-2 text-xs">
              {['EUR_USD', 'GBP_USD', 'AUD_USD', 'USD_JPY'].map((pair, index) => (
                <div key={pair} className="text-center">
                  <div className="font-medium text-gray-700 dark:text-gray-300 mb-1">{pair}</div>
                  <div className="h-8 bg-green-100 dark:bg-green-900 rounded flex items-center justify-center">
                    <span className="text-green-800 dark:text-green-200">
                      {mounted ? `0.${index + 1}` : '0.0'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Threshold: 0.4 | No breaches detected
            </div>
          </div>
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

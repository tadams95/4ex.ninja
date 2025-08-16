/**
 * Regime Data Provider Component - Client-side only wrapper
 */

'use client';

import { PerformanceByRegime } from '../../components/PerformanceByRegime';
import { RegimeMonitor } from '../../components/RegimeMonitor';
import { StrategyHealthPanel } from '../../components/StrategyHealthPanel';
import { useRegimeData } from '../../hooks/useRegimeData';

export default function RegimeDataProvider() {
  const {
    regimeStatus,
    alerts,
    strategyHealth,
    performanceSummary,
    loading,
    error,
    lastUpdate,
    refetch,
    acknowledgeAlert,
  } = useRegimeData();

  return (
    <div className="min-h-screen bg-neutral-900 text-white">
      {/* Header */}
      <div className="border-b border-neutral-700 bg-neutral-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div>
              <h1 className="text-2xl font-bold text-white">Regime Monitoring</h1>
              <p className="text-sm text-neutral-400">Phase 2 Real-Time Market Analysis</p>
            </div>
            <div className="flex items-center space-x-4">
              {error && (
                <div className="flex items-center text-red-400 text-sm">
                  <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
                  API Error
                </div>
              )}
              <button
                onClick={refetch}
                disabled={loading}
                className="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-neutral-600 rounded transition-colors"
              >
                {loading ? 'Refreshing...' : 'Refresh'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Debug Info for Development */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mb-6 p-4 bg-blue-900/20 border border-blue-500/30 rounded-lg">
            <h3 className="text-sm font-medium text-blue-400 mb-2">Debug Information</h3>
            <div className="text-xs text-blue-300 space-y-1">
              <div>
                API URL:{' '}
                {process.env.NEXT_PUBLIC_MONITORING_API_URL || 'http://157.230.58.248:8081'}
              </div>
              <div>Loading: {loading ? 'Yes' : 'No'}</div>
              <div>Error: {error || 'None'}</div>
              <div>Regime Status: {regimeStatus ? 'Loaded' : 'Not loaded'}</div>
              <div>Alerts Count: {alerts.length}</div>
              <div>Last Update: {lastUpdate.toISOString()}</div>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 bg-red-900/20 border border-red-500/30 rounded-lg">
            <div className="flex items-center">
              <div className="w-4 h-4 bg-red-500 rounded-full mr-3"></div>
              <div>
                <h3 className="text-sm font-medium text-red-400">Connection Error</h3>
                <p className="text-sm text-red-300 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Regime Monitor */}
          <div className="lg:col-span-1">
            <RegimeMonitor regimeStatus={regimeStatus} loading={loading} lastUpdate={lastUpdate} />
          </div>

          {/* Middle Column - Performance */}
          <div className="lg:col-span-1">
            <PerformanceByRegime performanceSummary={performanceSummary} loading={loading} />
          </div>

          {/* Right Column - Health & Alerts */}
          <div className="lg:col-span-1">
            <StrategyHealthPanel
              strategyHealth={strategyHealth}
              alerts={alerts}
              loading={loading}
              onAcknowledgeAlert={acknowledgeAlert}
            />
          </div>
        </div>

        {/* Status Bar */}
        <div className="mt-8 p-4 bg-neutral-800 rounded-lg border border-neutral-700">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-6">
              <div className="flex items-center">
                <div
                  className={`w-2 h-2 rounded-full mr-2 ${!error ? 'bg-green-500' : 'bg-red-500'}`}
                ></div>
                <span className="text-neutral-400">
                  API Status: {!error ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                <span className="text-neutral-400">
                  Last Update: {lastUpdate.toLocaleTimeString()}
                </span>
              </div>
              {alerts.filter(alert => !alert.acknowledged).length > 0 && (
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full mr-2 animate-pulse"></div>
                  <span className="text-yellow-400">
                    {alerts.filter(alert => !alert.acknowledged).length} unread alerts
                  </span>
                </div>
              )}
            </div>
            <div className="text-neutral-500">4ex.ninja Phase 2 Monitoring v2.0</div>
          </div>
        </div>
      </div>
    </div>
  );
}

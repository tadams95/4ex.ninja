/**
 * Regime Monitoring Dashboard Page
 * Phase 2 Real-Time Monitoring Dashboard Frontend
 */

'use client';

import dynamic from 'next/dynamic';
import { ExportControls } from '../../components/ExportControls';
import { PerformanceByRegime } from '../../components/PerformanceByRegime';
import { RegimeChart } from '../../components/RegimeChart';
import { RegimeMonitor } from '../../components/RegimeMonitor';
import { StrategyHealthPanel } from '../../components/StrategyHealthPanel';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { useRegimeData } from '../../hooks/useRegimeData';

// Create a dynamic component to ensure client-only rendering
const DynamicDashboard = dynamic(() => Promise.resolve(ClientSideDashboard), {
  ssr: false,
  loading: () => (
    <div className="min-h-screen bg-black text-white">
      <div className="border-b border-neutral-700 bg-black">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div>
              <h1 className="text-2xl font-bold text-white">Regime Monitoring</h1>
              <p className="text-sm text-neutral-400">Phase 2 Real-Time Market Analysis</p>
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
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-lg h-64"></div>
          <div className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-lg h-64"></div>
          <div className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-lg h-64"></div>
        </div>
      </div>
    </div>
  ),
});

function ClientSideDashboard() {
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
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <div className="border-b border-neutral-700 bg-black">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div>
              <h1 className="text-2xl font-bold text-white">Regime Monitoring</h1>
              {/* <p className="text-sm text-neutral-400">Phase 2 Real-Time Market Analysis</p> */}
            </div>
            <div className="flex items-center space-x-4">
              {error && (
                <div className="flex items-center text-red-400 text-sm">
                  <div className="w-2 h-2 bg-red-500 rounded-full mr-2 animate-pulse"></div>
                  API Error
                </div>
              )}
              <Button
                onClick={refetch}
                disabled={loading}
                variant="primary"
                size="sm"
                loading={loading}
              >
                Refresh
              </Button>
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
          <Card variant="outlined" padding="md" className="mb-6 border-red-500/30 bg-red-900/10">
            <div className="flex items-center p-2">
              <div className="w-4 h-4 bg-red-500 rounded-full mr-3 animate-pulse"></div>
              <div>
                <h3 className="text-sm font-medium text-red-400">Connection Error</h3>
                <p className="text-sm text-red-300 mt-1">{error}</p>
                <p className="text-xs text-red-400 mt-2">
                  Please check your network connection and try refreshing the page.
                </p>
              </div>
            </div>
          </Card>
        )}

        {/* Live Data Indicator & Export Controls */}
        <div className="mb-8 p-5 bg-neutral-800 rounded-lg border border-neutral-700 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                <span className="text-green-400 font-medium text-sm">Live Market Data</span>
              </div>
              <div className="text-neutral-400 text-sm">OANDA Demo API • Updates every 30s</div>
            </div>

            {/* Export Controls */}
            <ExportControls className="ml-4" />
          </div>
        </div>

        {/* Dashboard Grid - Main Monitoring Panels */}
        <div className="mb-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Regime Monitor */}
            <div className="lg:col-span-1">
              <RegimeMonitor
                regimeStatus={regimeStatus}
                loading={loading}
                lastUpdate={lastUpdate}
              />
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
        </div>

        {/* Chart Section - Visual Analytics */}
        <div className="mb-8">
          <div className="mb-4">
            <h2 className="text-xl font-semibold text-white mb-2">Market Regime Analytics</h2>
            <p className="text-sm text-neutral-400">
              Historical regime patterns and timeline visualization
            </p>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <div className="bg-neutral-800 rounded-lg border border-neutral-700 p-6 shadow-lg">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-white mb-2">24-Hour Regime Timeline</h3>
                <p className="text-sm text-neutral-400">
                  Recent regime transitions and market dynamics
                </p>
              </div>
              <RegimeChart timeframe="24h" />
            </div>

            <div className="bg-neutral-800 rounded-lg border border-neutral-700 p-6 shadow-lg">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-white mb-2">Weekly Regime Overview</h3>
                <p className="text-sm text-neutral-400">
                  Broader market regime patterns and trends
                </p>
              </div>
              <RegimeChart timeframe="7d" />
            </div>
          </div>
        </div>

        {/* Status Bar - System Information */}
        <div className="mt-6 p-5 bg-neutral-800 rounded-lg border border-neutral-700 shadow-lg">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-6">
              <div className="flex items-center">
                <div
                  className={`w-2 h-2 rounded-full mr-3 ${!error ? 'bg-green-500' : 'bg-red-500'}`}
                ></div>
                <span className="text-neutral-400 font-medium">
                  API Status: {!error ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
                <span className="text-neutral-400">
                  Last Update: {lastUpdate.toLocaleTimeString()}
                </span>
              </div>
              {alerts.filter((alert: any) => !alert.acknowledged).length > 0 && (
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full mr-3 animate-pulse"></div>
                  <span className="text-yellow-400 font-medium">
                    {alerts.filter((alert: any) => !alert.acknowledged).length} unread alerts
                  </span>
                </div>
              )}
            </div>
            <div className="text-neutral-500 font-medium">4ex.ninja Phase 2 Monitoring v2.0</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function RegimeMonitoringPage() {
  return <DynamicDashboard />;
}

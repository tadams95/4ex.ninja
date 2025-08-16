/**
 * Regime Monitoring Dashboard Page
 * Phase 2 Real-Time Monitoring Dashboard Frontend
 */

'use client';

import dynamic from 'next/dynamic';
import { PerformanceByRegime } from '../../components/PerformanceByRegime';
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
            <div className="flex items-center">
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
        )}{' '}
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
              {alerts.filter((alert: any) => !alert.acknowledged).length > 0 && (
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full mr-2 animate-pulse"></div>
                  <span className="text-yellow-400">
                    {alerts.filter((alert: any) => !alert.acknowledged).length} unread alerts
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

export default function RegimeMonitoringPage() {
  return <DynamicDashboard />;
}

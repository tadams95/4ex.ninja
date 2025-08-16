/**
 * Client-Side Dashboard Component
 * Handles all data fetching and rendering client-side only
 */

'use client';

import { MonitoringHealthStatus } from '../../components/MonitoringHealthStatus';
import { PerformanceByRegime } from '../../components/PerformanceByRegime';
import { RegimeMonitor } from '../../components/RegimeMonitor';
import { StrategyHealthPanel } from '../../components/StrategyHealthPanel';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { useRegimeData } from '../../hooks/useRegimeData';

export default function ClientSideDashboard() {
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
              <p className="text-sm text-neutral-400">Phase 2 Real-Time Market Analysis</p>
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
        {/* Monitoring Service Health Status */}
        <div className="mb-6">
          <MonitoringHealthStatus
            showDetails={true}
            className="bg-neutral-800 border-neutral-600"
          />
        </div>

        {/* Debug Info for Development */}
        {process.env.NODE_ENV === 'development' && (
          <Card variant="outlined" padding="md" className="mb-6 border-blue-500/30 bg-blue-900/10">
            <h3 className="text-sm font-medium text-blue-400 mb-3">Debug Information</h3>
            <div className="text-xs text-blue-300 space-y-2">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                <div>
                  <span className="text-blue-400">API URL:</span>{' '}
                  <span className="font-mono">
                    {process.env.NEXT_PUBLIC_MONITORING_API_URL ||
                      '/api/monitoring (auto-detected)'}
                  </span>
                </div>
                <div>
                  <span className="text-blue-400">Environment:</span>{' '}
                  {typeof window !== 'undefined' ? window.location.protocol : 'server'}
                </div>
                <div>
                  <span className="text-blue-400">HTTPS:</span>{' '}
                  {typeof window !== 'undefined' && window.location.protocol === 'https:'
                    ? 'Yes (using proxy)'
                    : 'No (direct connection)'}
                </div>
                <div>
                  <span className="text-blue-400">Loading:</span> {loading ? 'Yes' : 'No'}
                </div>
                <div>
                  <span className="text-blue-400">Error:</span>{' '}
                  <span className={error ? 'text-red-400' : ''}>{error || 'None'}</span>
                </div>
                <div>
                  <span className="text-blue-400">Regime Status:</span>{' '}
                  {regimeStatus ? 'Loaded' : 'Not loaded'}
                </div>
                <div>
                  <span className="text-blue-400">Alerts:</span> {alerts.length}
                </div>
                <div>
                  <span className="text-blue-400">Last Update:</span>{' '}
                  <span className="font-mono">{lastUpdate.toISOString()}</span>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-blue-500/20">
                <a
                  href="/api/monitoring-health"
                  target="_blank"
                  className="text-xs text-blue-400 hover:text-blue-300 underline transition-colors"
                >
                  Test Proxy Health Check →
                </a>
              </div>
            </div>
          </Card>
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
        <Card variant="elevated" padding="md" className="mt-8">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-6">
              <div className="flex items-center">
                <div
                  className={`w-2 h-2 rounded-full mr-2 ${
                    !error ? 'bg-green-500' : 'bg-red-500 animate-pulse'
                  }`}
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
            <div className="text-neutral-500 font-medium">4ex.ninja Phase 2 Monitoring v2.0</div>
          </div>
        </Card>
      </div>
    </div>
  );
}

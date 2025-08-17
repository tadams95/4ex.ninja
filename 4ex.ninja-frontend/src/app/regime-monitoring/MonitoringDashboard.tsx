/**
 * Monitoring Dashboard Component - Client-side only
 */

'use client';

import { ExportControls } from '../../components/ExportControls';
import { PerformanceByRegime } from '../../components/PerformanceByRegime';
import { RegimeChart } from '../../components/RegimeChart';
import { RegimeMonitor } from '../../components/RegimeMonitor';
import { StrategyHealthPanel } from '../../components/StrategyHealthPanel';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { Tooltip } from '../../components/ui/Tooltip';
import { useRegimeData } from '../../hooks/useRegimeData';

export default function MonitoringDashboard() {
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
              <Tooltip content="Real-time market regime detection and analysis system">
                <h1 className="text-2xl font-bold text-white cursor-help">Regime Monitoring</h1>
              </Tooltip>
              <p className="text-sm text-neutral-400">Phase 2 Real-Time Market Analysis</p>
            </div>
            <div className="flex items-center space-x-4">
              {error && (
                <Tooltip content="Connection to monitoring API failed. Data may be stale.">
                  <div className="flex items-center text-red-400 text-sm cursor-help">
                    <div className="w-2 h-2 bg-red-500 rounded-full mr-2 animate-pulse"></div>
                    API Error
                  </div>
                </Tooltip>
              )}
              <Tooltip content="Refresh all dashboard data from the monitoring API">
                <Button
                  onClick={refetch}
                  disabled={loading}
                  variant="primary"
                  size="sm"
                  loading={loading}
                >
                  Refresh
                </Button>
              </Tooltip>
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
        )}

        {/* Live Data Indicator & Export Controls */}
        <div className="mb-6 p-4 bg-neutral-800 rounded-lg border border-neutral-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Tooltip content="Green indicator shows live market data is flowing from OANDA API">
                <div className="flex items-center cursor-help">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                  <span className="text-green-400 font-medium">Live Market Data</span>
                </div>
              </Tooltip>
              <Tooltip content="Market data updates automatically every 30 seconds during trading hours">
                <div className="text-neutral-400 text-sm cursor-help">
                  OANDA Demo API • Updates every 30s
                </div>
              </Tooltip>
            </div>

            {/* Export Controls */}
            <Tooltip content="Download regime and performance data as CSV or JSON files">
              <div>
                <ExportControls className="ml-4" />
              </div>
            </Tooltip>
          </div>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Left Column - Regime Monitor */}
          <Tooltip content="Current market regime classification with confidence levels and timing">
            <div className="lg:col-span-1 cursor-help">
              <RegimeMonitor
                regimeStatus={regimeStatus}
                loading={loading}
                lastUpdate={lastUpdate}
              />
            </div>
          </Tooltip>

          {/* Middle Column - Performance */}
          <Tooltip content="Performance analytics broken down by different market regime types">
            <div className="lg:col-span-1 cursor-help">
              <PerformanceByRegime performanceSummary={performanceSummary} loading={loading} />
            </div>
          </Tooltip>

          {/* Right Column - Health & Alerts */}
          <Tooltip content="System health monitoring and real-time alerts for regime changes">
            <div className="lg:col-span-1 cursor-help">
              <StrategyHealthPanel
                strategyHealth={strategyHealth}
                alerts={alerts}
                loading={loading}
                onAcknowledgeAlert={acknowledgeAlert}
              />
            </div>
          </Tooltip>
        </div>

        {/* Chart Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-neutral-800 rounded-lg border border-neutral-700 p-6">
            <Tooltip content="Visual timeline showing market regime changes over the last 24 hours">
              <h3 className="text-lg font-semibold text-white mb-4 cursor-help">
                24-Hour Regime Timeline
              </h3>
            </Tooltip>
            <RegimeChart timeframe="24h" />
          </div>

          <div className="bg-neutral-800 rounded-lg border border-neutral-700 p-6">
            <Tooltip content="Weekly overview of market regime patterns and transitions">
              <h3 className="text-lg font-semibold text-white mb-4 cursor-help">
                Weekly Regime Overview
              </h3>
            </Tooltip>
            <RegimeChart timeframe="7d" />
          </div>
        </div>

        {/* Status Bar */}
        <div className="mt-8 p-4 bg-neutral-800 rounded-lg border border-neutral-700">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-6">
              <Tooltip
                content={`API connection status: ${
                  !error
                    ? 'Successfully connected to monitoring services'
                    : 'Connection failed - check network or API status'
                }`}
              >
                <div className="flex items-center cursor-help">
                  <div
                    className={`w-2 h-2 rounded-full mr-2 ${
                      !error ? 'bg-green-500' : 'bg-red-500'
                    }`}
                  ></div>
                  <span className="text-neutral-400">
                    API Status: {!error ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
              </Tooltip>
              <Tooltip content="Timestamp of the most recent data update from the monitoring API">
                <div className="flex items-center cursor-help">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                  <span className="text-neutral-400">
                    Last Update: {lastUpdate.toLocaleTimeString()}
                  </span>
                </div>
              </Tooltip>
              {alerts.filter(alert => !alert.acknowledged).length > 0 && (
                <Tooltip content="Click on alerts in the Strategy Health panel to acknowledge them">
                  <div className="flex items-center cursor-help">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full mr-2 animate-pulse"></div>
                    <span className="text-yellow-400">
                      {alerts.filter(alert => !alert.acknowledged).length} unread alerts
                    </span>
                  </div>
                </Tooltip>
              )}
            </div>
            <Tooltip content="4ex.ninja Phase 2 Market Regime Monitoring System">
              <div className="text-neutral-500 cursor-help">4ex.ninja Phase 2 Monitoring v2.0</div>
            </Tooltip>
          </div>
        </div>
      </div>
    </div>
  );
}

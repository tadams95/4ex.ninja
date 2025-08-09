/**
 * Real-time Performance Dashboard Component
 *
 * Displays live performance metrics for task 1.10.6.3: Real-time performance optimization
 */

'use client';

import { getPerformanceSummary } from '@/utils/performance';
import { useEffect, useState } from 'react';

interface PerformanceMetrics {
  vitals: Record<string, number>;
  customMetrics: Record<string, number>;
  budgets: Array<{
    name: string;
    threshold: number;
    unit: string;
    current?: number;
    status: 'good' | 'needs-improvement' | 'poor';
  }>;
  sessionId: string;
}

export function RealTimePerformanceDashboard({
  enabled = true,
  updateInterval = 5000,
}: {
  enabled?: boolean;
  updateInterval?: number;
}) {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    if (!enabled) return;

    const updateMetrics = () => {
      const summary = getPerformanceSummary();
      setMetrics(summary);
      setLastUpdate(new Date());
    };

    // Initial update
    updateMetrics();

    // Set up interval for real-time updates
    const interval = setInterval(updateMetrics, updateInterval);

    return () => clearInterval(interval);
  }, [enabled, updateInterval]);

  if (!enabled || !metrics) {
    return null;
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good':
        return 'text-green-600 bg-green-100';
      case 'needs-improvement':
        return 'text-yellow-600 bg-yellow-100';
      case 'poor':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatValue = (value: number, unit: string) => {
    if (unit === 'ms') {
      return `${Math.round(value)}ms`;
    } else if (unit === 'score') {
      return `${Math.round(value * 10) / 10}`;
    } else {
      return `${Math.round(value * 10) / 10}${unit}`;
    }
  };

  return (
    <div className="fixed bottom-4 right-4 w-96 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Real-time Performance Monitor</h3>
        <p className="text-sm text-gray-500">Last updated: {lastUpdate?.toLocaleTimeString()}</p>
      </div>

      <div className="p-4 space-y-4">
        {/* Web Vitals */}
        {Object.keys(metrics.vitals).length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Web Vitals</h4>
            <div className="space-y-1">
              {Object.entries(metrics.vitals).map(([name, value]) => (
                <div key={name} className="flex justify-between text-xs">
                  <span className="text-gray-600">{name}:</span>
                  <span className="font-mono">{Math.round(value)}ms</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Performance Budgets */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Performance Budgets</h4>
          <div className="space-y-2">
            {metrics.budgets.map(budget => (
              <div key={budget.name} className="space-y-1">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-600">{budget.name}</span>
                  <span className={`text-xs px-2 py-1 rounded ${getStatusColor(budget.status)}`}>
                    {budget.status}
                  </span>
                </div>
                {budget.current !== undefined && (
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">
                      Current: {formatValue(budget.current, budget.unit)}
                    </span>
                    <span className="text-gray-500">
                      Target: {formatValue(budget.threshold, budget.unit)}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Real-time Metrics (1.10.6.3) */}
        {Object.keys(metrics.customMetrics).length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Real-time Metrics</h4>
            <div className="space-y-1">
              {Object.entries(metrics.customMetrics).map(([name, value]) => {
                if (
                  name.includes('react_query_cache_hit') ||
                  name.includes('websocket_') ||
                  name.includes('animation_') ||
                  name.includes('trading_flow_') ||
                  name.includes('subscription_')
                ) {
                  return (
                    <div key={name} className="flex justify-between text-xs">
                      <span className="text-gray-600">
                        {name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                      </span>
                      <span className="font-mono">
                        {name.includes('cache_hit')
                          ? `${Math.round(value)}%`
                          : name.includes('frame_rate')
                          ? `${Math.round(value)}fps`
                          : `${Math.round(value)}ms`}
                      </span>
                    </div>
                  );
                }
                return null;
              })}
            </div>
          </div>
        )}

        {/* Session Info */}
        <div className="pt-2 border-t border-gray-100">
          <div className="text-xs text-gray-500">
            Session ID: <span className="font-mono">{metrics.sessionId.slice(-8)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Performance Alert Component
 * Shows alerts when performance budgets are exceeded
 */
export function PerformanceAlerts() {
  const [alerts, setAlerts] = useState<Array<{ id: string; message: string; severity: string }>>(
    []
  );

  useEffect(() => {
    const checkAlerts = () => {
      const summary = getPerformanceSummary();
      const newAlerts: Array<{ id: string; message: string; severity: string }> = [];

      summary.budgets.forEach(budget => {
        if (budget.status === 'poor' && budget.current !== undefined) {
          newAlerts.push({
            id: `${budget.name}-${Date.now()}`,
            message: `${budget.name} performance is poor: ${budget.current} > ${budget.threshold}`,
            severity: 'error',
          });
        } else if (budget.status === 'needs-improvement' && budget.current !== undefined) {
          newAlerts.push({
            id: `${budget.name}-${Date.now()}`,
            message: `${budget.name} needs improvement: ${budget.current} > ${budget.threshold}`,
            severity: 'warning',
          });
        }
      });

      setAlerts(newAlerts);
    };

    const interval = setInterval(checkAlerts, 10000); // Check every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const removeAlert = (id: string) => {
    setAlerts(alerts => alerts.filter(alert => alert.id !== id));
  };

  if (alerts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 space-y-2 z-50">
      {alerts.map(alert => (
        <div
          key={alert.id}
          className={`p-3 rounded-lg shadow-lg max-w-sm ${
            alert.severity === 'error'
              ? 'bg-red-100 border border-red-200 text-red-800'
              : 'bg-yellow-100 border border-yellow-200 text-yellow-800'
          }`}
        >
          <div className="flex justify-between items-start">
            <p className="text-sm">{alert.message}</p>
            <button
              onClick={() => removeAlert(alert.id)}
              className="ml-2 text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

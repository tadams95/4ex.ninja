/**
 * StrategyHealthPanel Component
 * Displays strategy health metrics, alerts, and warnings
 */

'use client';

import React from 'react';
import { type Alert, type StrategyHealth } from '../hooks/useRegimeData';
import { Card } from './ui/Card';

interface StrategyHealthPanelProps {
  strategyHealth: StrategyHealth | null;
  alerts: Alert[];
  loading: boolean;
  onAcknowledgeAlert: (alertId: string) => void;
}

const getHealthColor = (score: number): string => {
  if (score >= 0.8) return 'text-green-400';
  if (score >= 0.6) return 'text-yellow-400';
  if (score >= 0.4) return 'text-orange-400';
  return 'text-red-400';
};

const getHealthStatus = (score: number): string => {
  if (score >= 0.8) return 'Excellent';
  if (score >= 0.6) return 'Good';
  if (score >= 0.4) return 'Fair';
  return 'Poor';
};

const getSeverityColor = (severity: 'info' | 'warning' | 'critical'): string => {
  const colors = {
    info: 'text-blue-400 bg-blue-900/20 border-blue-500/30',
    warning: 'text-yellow-400 bg-yellow-900/20 border-yellow-500/30',
    critical: 'text-red-400 bg-red-900/20 border-red-500/30',
  };
  return colors[severity];
};

const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
  return date.toLocaleDateString();
};

export const StrategyHealthPanel: React.FC<StrategyHealthPanelProps> = ({
  strategyHealth,
  alerts,
  loading,
  onAcknowledgeAlert,
}) => {
  if (loading) {
    return (
      <Card className="animate-pulse">
        <div className="h-6 bg-neutral-600 rounded mb-4"></div>
        <div className="h-20 bg-neutral-600 rounded mb-4"></div>
        <div className="space-y-2">
          <div className="h-4 bg-neutral-600 rounded"></div>
          <div className="h-4 bg-neutral-600 rounded w-3/4"></div>
        </div>
      </Card>
    );
  }

  const unacknowledgedAlerts = alerts.filter(alert => !alert.acknowledged);

  return (
    <div className="space-y-4">
      {/* Strategy Health Status */}
      <Card className="border border-neutral-600">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Strategy Health</h3>
          {strategyHealth && (
            <div className="text-right">
              <div className={`text-sm font-medium ${getHealthColor(strategyHealth.health_score)}`}>
                {getHealthStatus(strategyHealth.health_score)}
              </div>
              <div className="text-xs text-neutral-400">
                Score: {Math.round(strategyHealth.health_score * 100)}%
              </div>
            </div>
          )}
        </div>

        {strategyHealth ? (
          <>
            {/* Health Score Visualization */}
            <div className="mb-6">
              <div className="flex items-center mb-2">
                <span className="text-sm text-neutral-400 mr-2">Health Score</span>
                <div className="flex-1 bg-neutral-600 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all duration-300 ${
                      strategyHealth.health_score >= 0.8
                        ? 'bg-green-500'
                        : strategyHealth.health_score >= 0.6
                        ? 'bg-yellow-500'
                        : strategyHealth.health_score >= 0.4
                        ? 'bg-orange-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${strategyHealth.health_score * 100}%` }}
                  ></div>
                </div>
                <span
                  className={`text-sm font-medium ml-2 ${getHealthColor(
                    strategyHealth.health_score
                  )}`}
                >
                  {Math.round(strategyHealth.health_score * 100)}%
                </span>
              </div>
            </div>

            {/* Warnings */}
            {strategyHealth.warnings.length > 0 && (
              <div className="mb-4">
                <h4 className="text-sm font-medium text-neutral-300 mb-2">Active Warnings</h4>
                <div className="space-y-2">
                  {strategyHealth.warnings.map((warning, index) => (
                    <div
                      key={index}
                      className="flex items-center text-sm text-yellow-400 bg-yellow-900/20 border border-yellow-500/30 rounded px-3 py-2"
                    >
                      <div className="w-1.5 h-1.5 bg-yellow-400 rounded-full mr-2 flex-shrink-0"></div>
                      {warning}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Last Update */}
            <div className="text-xs text-neutral-500">
              Last updated: {new Date(strategyHealth.last_update).toLocaleString()}
            </div>
          </>
        ) : (
          <div className="text-center py-4">
            <div className="text-red-400 mb-2">Health monitoring unavailable</div>
            <div className="text-neutral-400 text-sm">Check API connection</div>
          </div>
        )}
      </Card>

      {/* Recent Alerts */}
      <Card className="border border-neutral-600">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Recent Alerts</h3>
          {unacknowledgedAlerts.length > 0 && (
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-red-400">{unacknowledgedAlerts.length} unread</span>
            </div>
          )}
        </div>

        {alerts.length === 0 ? (
          <div className="text-center py-6 text-neutral-400">No recent alerts</div>
        ) : (
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {alerts.slice(0, 5).map(alert => (
              <div
                key={alert.id}
                className={`border rounded-lg p-3 ${getSeverityColor(alert.severity)} ${
                  alert.acknowledged ? 'opacity-60' : ''
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="text-sm font-medium">{alert.title}</span>
                      <span className="text-xs px-2 py-0.5 bg-black/20 rounded">
                        {alert.alert_type}
                      </span>
                    </div>
                    <p className="text-sm opacity-90 mb-2">{alert.message}</p>
                    <div className="text-xs opacity-75">{formatTimestamp(alert.timestamp)}</div>
                  </div>
                  {!alert.acknowledged && (
                    <button
                      onClick={() => onAcknowledgeAlert(alert.id)}
                      className="ml-2 text-xs px-2 py-1 bg-white/10 hover:bg-white/20 rounded transition-colors"
                    >
                      Acknowledge
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

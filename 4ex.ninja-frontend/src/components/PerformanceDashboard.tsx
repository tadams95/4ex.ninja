/**
 * Performance Dashboard Component
 *
 * Displays real-time performance metrics, Web Vitals,
 * and performance budget status for monitoring and debugging.
 */

'use client';

import { performanceMonitor, type PerformanceBudget } from '@/utils/performance';
import { useEffect, useState } from 'react';

interface PerformanceDashboardProps {
  isVisible?: boolean;
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
}

interface PerformanceData {
  vitals: Record<string, number>;
  customMetrics: Record<string, number>;
  budgets: PerformanceBudget[];
  sessionId: string;
}

export default function PerformanceDashboard({
  isVisible = false,
  position = 'bottom-right',
}: PerformanceDashboardProps) {
  const [performanceData, setPerformanceData] = useState<PerformanceData | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    if (!isVisible) return;

    // Update performance data every 5 seconds
    const updateData = () => {
      const data = performanceMonitor.getPerformanceSummary();
      setPerformanceData(data);
    };

    updateData();
    const interval = setInterval(updateData, 5000);

    return () => clearInterval(interval);
  }, [isVisible]);

  if (!isVisible || !performanceData) return null;

  const positionClasses = {
    'top-left': 'top-4 left-4',
    'top-right': 'top-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'bottom-right': 'bottom-4 right-4',
  };

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
    }
    if (unit === 'score') {
      return value.toFixed(3);
    }
    return Math.round(value).toString();
  };

  return (
    <div className={`fixed ${positionClasses[position]} z-50`}>
      <div className="bg-white border border-gray-300 rounded-lg shadow-lg min-w-[300px] max-w-[400px]">
        {/* Header */}
        <div
          className="px-4 py-2 bg-gray-50 rounded-t-lg border-b border-gray-200 cursor-pointer flex justify-between items-center"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <h3 className="text-sm font-semibold text-gray-800">Performance Monitor</h3>
          <span className="text-xs text-gray-500">{isExpanded ? '▼' : '▶'}</span>
        </div>

        {isExpanded && (
          <div className="p-4 space-y-4 max-h-[500px] overflow-y-auto">
            {/* Web Vitals */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Core Web Vitals</h4>
              <div className="space-y-2">
                {Object.entries(performanceData.vitals).map(([vital, value]) => {
                  const budget = performanceData.budgets.find(b => b.name === vital);
                  return (
                    <div key={vital} className="flex justify-between items-center text-xs">
                      <span className="text-gray-600">{vital}:</span>
                      <span
                        className={`px-2 py-1 rounded ${
                          budget ? getStatusColor(budget.status) : 'text-gray-800'
                        }`}
                      >
                        {formatValue(value, vital === 'CLS' ? 'score' : 'ms')}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Performance Budgets */}
            {performanceData.budgets.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Performance Budgets</h4>
                <div className="space-y-2">
                  {performanceData.budgets.map(budget => (
                    <div key={budget.name} className="text-xs">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-gray-600">{budget.name}</span>
                        <span className={`px-2 py-1 rounded ${getStatusColor(budget.status)}`}>
                          {budget.current ? formatValue(budget.current, budget.unit) : 'N/A'}
                        </span>
                      </div>
                      {budget.current && (
                        <div className="bg-gray-200 rounded-full h-1">
                          <div
                            className={`h-1 rounded-full ${
                              budget.status === 'good'
                                ? 'bg-green-500'
                                : budget.status === 'needs-improvement'
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                            }`}
                            style={{
                              width: `${Math.min(
                                (budget.current / (budget.threshold * 2)) * 100,
                                100
                              )}%`,
                            }}
                          />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Custom Metrics */}
            {Object.keys(performanceData.customMetrics).length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Trading Metrics</h4>
                <div className="space-y-2">
                  {Object.entries(performanceData.customMetrics).map(([metric, value]) => (
                    <div key={metric} className="flex justify-between items-center text-xs">
                      <span className="text-gray-600 capitalize">{metric.replace(/_/g, ' ')}:</span>
                      <span className="text-gray-800">{formatValue(value, 'ms')}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Session Info */}
            <div className="border-t border-gray-200 pt-2">
              <div className="text-xs text-gray-500">
                Session: {performanceData.sessionId.slice(-8)}
              </div>
            </div>
          </div>
        )}

        {/* Mini view when collapsed */}
        {!isExpanded && (
          <div className="p-2">
            <div className="flex space-x-2">
              {performanceData.budgets.slice(0, 3).map(budget => (
                <div
                  key={budget.name}
                  className={`px-2 py-1 rounded text-xs ${getStatusColor(budget.status)}`}
                >
                  {budget.name.substring(0, 3)}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

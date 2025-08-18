import { useRiskData } from '@/hooks/useRiskData';
import { useEffect } from 'react';
import { registerRefetchCallback } from './RiskDashboard';

interface CorrelationHeatMapProps {
  refreshInterval?: number;
}

export default function CorrelationHeatMap({ refreshInterval = 30000 }: CorrelationHeatMapProps) {
  const { correlationData, loading, error, lastUpdate, refetch } = useRiskData(refreshInterval);

  // Register refetch callback with parent dashboard
  useEffect(() => {
    return registerRefetchCallback(refetch);
  }, [refetch]);

  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const getCorrelationColor = (value: number | null): string => {
    if (value === null) return 'bg-neutral-600';

    const absValue = Math.abs(value);
    if (absValue >= 0.8) return value > 0 ? 'bg-red-600' : 'bg-blue-600';
    if (absValue >= 0.6) return value > 0 ? 'bg-red-400' : 'bg-blue-400';
    if (absValue >= 0.4) return value > 0 ? 'bg-red-200' : 'bg-blue-200';
    if (absValue >= 0.2) return value > 0 ? 'bg-red-100' : 'bg-blue-100';
    return 'bg-neutral-500';
  };

  const getTextColor = (value: number | null): string => {
    if (value === null) return 'text-neutral-300';

    const absValue = Math.abs(value);
    if (absValue >= 0.6) return 'text-white';
    if (absValue >= 0.4) return 'text-gray-800';
    return 'text-gray-900';
  };

  if (loading) {
    return (
      <div className="p-6 bg-neutral-800 rounded-lg border border-neutral-700 shadow-lg">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-white mb-1">Correlation Matrix</h3>
          <p className="text-sm text-neutral-400">Loading correlation data...</p>
        </div>

        <div className="animate-pulse">
          <div className="grid grid-cols-4 gap-2">
            {Array.from({ length: 16 }).map((_, i) => (
              <div key={i} className="h-12 bg-neutral-600 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-neutral-800 rounded-lg border border-red-500/30 shadow-lg">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-red-400 mb-1">Correlation Matrix - Error</h3>
          <p className="text-sm text-red-300">{error}</p>
        </div>

        <button
          onClick={refetch}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!correlationData) {
    return (
      <div className="p-6 bg-neutral-800 rounded-lg border border-neutral-700 shadow-lg">
        <h3 className="text-lg font-semibold text-white mb-1">Correlation Matrix</h3>
        <p className="text-sm text-neutral-400">No correlation data available</p>
      </div>
    );
  }

  const pairs = Object.keys(correlationData.matrix);
  const highCorrelations = correlationData.risk_alerts.high_correlations || [];

  return (
    <div className="p-6 bg-neutral-800 rounded-lg border border-neutral-700 shadow-lg">
      {/* Header */}
      <div className="mb-4">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-semibold text-white mb-1">Correlation Matrix</h3>
            <p className="text-sm text-neutral-400">
              Last updated: {formatTime(lastUpdate)} | High Correlations:{' '}
              <span
                className={`font-semibold ${
                  highCorrelations.length > 0 ? 'text-red-400' : 'text-green-400'
                }`}
              >
                {highCorrelations.length}
              </span>
            </p>
          </div>
          <button
            onClick={refetch}
            className="px-3 py-1 text-sm bg-neutral-700 text-neutral-300 rounded hover:bg-neutral-600 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Risk Alerts */}
      {highCorrelations.length > 0 && (
        <div className="mb-4 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
          <div className="flex items-center mb-2">
            <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
            <span className="font-medium text-red-400">High Correlation Alert</span>
          </div>
          <div className="text-sm text-red-300">
            Threshold: {(correlationData.risk_alerts.threshold * 100).toFixed(0)}% | Breaches:{' '}
            {correlationData.risk_alerts.breach_count}
          </div>
          <div className="text-xs text-red-400 mt-1">{highCorrelations.join(', ')}</div>
        </div>
      )}

      {/* Correlation Matrix Grid */}
      <div className="mb-4">
        <div className="overflow-x-auto">
          <div className="min-w-full">
            {/* Header Row */}
            <div
              className="grid gap-1 mb-1"
              style={{ gridTemplateColumns: `80px repeat(${pairs.length}, 1fr)` }}
            >
              <div></div>
              {pairs.map(pair => (
                <div key={pair} className="text-xs font-medium text-neutral-300 text-center p-1">
                  {pair.replace('_', '/')}
                </div>
              ))}
            </div>

            {/* Matrix Rows */}
            {pairs.map(rowPair => (
              <div
                key={rowPair}
                className="grid gap-1 mb-1"
                style={{ gridTemplateColumns: `80px repeat(${pairs.length}, 1fr)` }}
              >
                <div className="text-xs font-medium text-neutral-300 p-1 text-right pr-2">
                  {rowPair.replace('_', '/')}
                </div>
                {pairs.map(colPair => {
                  const value = correlationData.matrix[rowPair]?.[colPair];
                  return (
                    <div
                      key={colPair}
                      className={`
                        text-xs font-medium text-center p-1 rounded
                        ${getCorrelationColor(value)}
                        ${getTextColor(value)}
                        transition-colors
                      `}
                      title={`${rowPair} vs ${colPair}: ${
                        value !== null ? (value * 100).toFixed(1) + '%' : 'N/A'
                      }`}
                    >
                      {value !== null ? (value * 100).toFixed(0) : '--'}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Color Legend */}
      <div className="mb-4">
        <div className="text-sm font-medium text-neutral-300 mb-2">Correlation Strength</div>
        <div className="flex items-center space-x-4 text-xs">
          <div className="flex items-center">
            <div className="w-4 h-4 bg-red-600 rounded mr-1"></div>
            <span className="text-neutral-400">Strong Positive (≥80%)</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-red-200 rounded mr-1"></div>
            <span className="text-neutral-400">Moderate Positive (40-79%)</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-gray-100 rounded mr-1"></div>
            <span className="text-neutral-400">Weak (0-39%)</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-blue-200 rounded mr-1"></div>
            <span className="text-neutral-400">Moderate Negative (-40 to -79%)</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-blue-600 rounded mr-1"></div>
            <span className="text-neutral-400">Strong Negative (≤-80%)</span>
          </div>
        </div>
      </div>

      {/* Pairs Analysis Summary */}
      {correlationData.pairs_analysis && correlationData.pairs_analysis.length > 0 && (
        <div className="border-t border-neutral-600 pt-4">
          <div className="text-sm font-medium text-neutral-300 mb-2">Average Correlations</div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {correlationData.pairs_analysis.slice(0, 6).map(analysis => (
              <div key={analysis.pair} className="flex justify-between">
                <span className="text-neutral-400">{analysis.pair.replace('_', '/')}:</span>
                <span
                  className={`font-medium ${
                    (analysis.average_correlation || 0) > 0.6
                      ? 'text-red-400'
                      : (analysis.average_correlation || 0) < -0.6
                      ? 'text-blue-400'
                      : 'text-neutral-300'
                  }`}
                >
                  {analysis.average_correlation !== null
                    ? `${(analysis.average_correlation * 100).toFixed(0)}%`
                    : 'N/A'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Status Footer */}
      <div className="mt-4 pt-3 border-t border-neutral-600">
        <div className="flex justify-between items-center text-xs text-neutral-400">
          <span>
            Matrix Size: {pairs.length}×{pairs.length}
          </span>
          <span
            className={`px-2 py-1 rounded-full text-xs font-medium ${
              correlationData.status === 'active'
                ? 'bg-green-900/30 text-green-400 border border-green-500/30'
                : 'bg-neutral-700 text-neutral-300 border border-neutral-600'
            }`}
          >
            {correlationData.status}
          </span>
        </div>
      </div>
    </div>
  );
}

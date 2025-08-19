'use client';

import { useCorrelationTrends } from '@/hooks/useCorrelationTrends';
import { useCallback, useEffect, useState } from 'react';
import {
  Brush,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { registerRefetchCallback } from './RiskDashboard';

interface CorrelationTrendsProps {
  refreshInterval?: number;
}

type TimePeriod = '1W' | '2W' | '1M';

const TIME_PERIOD_HOURS = {
  '1W': 7 * 24,
  '2W': 14 * 24,
  '1M': 30 * 24,
};

export default function CorrelationTrends({ refreshInterval = 30000 }: CorrelationTrendsProps) {
  const [selectedPeriod, setSelectedPeriod] = useState<TimePeriod>('1W');
  const [selectedPairs, setSelectedPairs] = useState<string[]>([]);
  const [showPredictions, setShowPredictions] = useState(true);
  const [showConfidenceInterval, setShowConfidenceInterval] = useState(true);

  // Use the correlation trends hook
  const { trendsData, forecastData, regimeData, loading, error, lastUpdate, refetch } =
    useCorrelationTrends(refreshInterval, TIME_PERIOD_HOURS[selectedPeriod]);

  // Register refetch callback
  useEffect(() => {
    return registerRefetchCallback(refetch);
  }, [refetch]);

  // Extract unique pairs and set initial selection
  useEffect(() => {
    const uniquePairs = [...new Set(trendsData.map(d => d.pair))];
    if (selectedPairs.length === 0 && uniquePairs.length > 0) {
      setSelectedPairs(uniquePairs.slice(0, 4)); // Show first 4 pairs by default
    }
  }, [trendsData, selectedPairs.length]);

  // Process data for chart
  const processChartData = useCallback(() => {
    if (!trendsData.length) return [];

    // Group by timestamp
    const dataByTime = trendsData.reduce((acc, item) => {
      const time = new Date(item.timestamp).toISOString();
      if (!acc[time]) {
        acc[time] = { timestamp: time, time_display: new Date(item.timestamp).toLocaleString() };
      }

      // Only include selected pairs
      if (selectedPairs.includes(item.pair)) {
        acc[time][item.pair] = item.correlation;
        if (showPredictions && item.predicted_correlation !== undefined) {
          acc[time][`${item.pair}_predicted`] = item.predicted_correlation;
        }
        if (showConfidenceInterval) {
          acc[time][`${item.pair}_upper`] = item.upper_bound;
          acc[time][`${item.pair}_lower`] = item.lower_bound;
        }
      }
      return acc;
    }, {} as Record<string, any>);

    return Object.values(dataByTime).sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  }, [trendsData, selectedPairs, showPredictions, showConfidenceInterval]);

  // Color scheme for different pairs
  const getColorForPair = (pair: string, index: number) => {
    const colors = [
      '#3b82f6',
      '#ef4444',
      '#10b981',
      '#f59e0b',
      '#8b5cf6',
      '#ec4899',
      '#06b6d4',
      '#84cc16',
    ];
    return colors[index % colors.length];
  };

  // Get trend direction indicator
  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'increasing':
        return '↗️';
      case 'decreasing':
        return '↘️';
      default:
        return '➡️';
    }
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null;

    return (
      <div className="bg-neutral-800 border border-neutral-600 rounded-lg p-3 shadow-lg">
        <p className="text-sm text-neutral-300 mb-2">{new Date(label).toLocaleString()}</p>
        {payload.map((entry: any, index: number) => {
          if (entry.dataKey.includes('_upper') || entry.dataKey.includes('_lower')) return null;

          const isPredicted = entry.dataKey.includes('_predicted');
          const pair = isPredicted ? entry.dataKey.replace('_predicted', '') : entry.dataKey;
          const trendItem = trendsData.find(
            d => d.pair === pair && new Date(d.timestamp).toISOString() === label
          );

          return (
            <div key={index} className="flex items-center justify-between space-x-3">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }} />
                <span className="text-sm text-white">
                  {pair} {isPredicted ? '(forecast)' : ''}
                </span>
                {trendItem && (
                  <span className="text-xs">{getTrendIcon(trendItem.trend_direction)}</span>
                )}
              </div>
              <span className="text-sm font-mono text-white">
                {(entry.value as number).toFixed(3)}
              </span>
            </div>
          );
        })}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="p-6 bg-neutral-800 rounded-lg border border-neutral-700 shadow-lg">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-white mb-1">Correlation Trends</h3>
          <p className="text-sm text-neutral-400">Loading trend analysis...</p>
        </div>
        <div className="animate-pulse h-64 bg-neutral-700 rounded" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-neutral-800 rounded-lg border border-red-500/30 shadow-lg">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-red-400 mb-1">Correlation Trends - Error</h3>
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

  const chartData = processChartData();
  const uniquePairs = [...new Set(trendsData.map(d => d.pair))];

  return (
    <div className="p-6 bg-neutral-800 rounded-lg border border-neutral-700 shadow-lg">
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-lg font-semibold text-white mb-1">Correlation Trends</h3>
            <p className="text-sm text-neutral-400">
              Historical correlation patterns and predictive analysis
            </p>
          </div>
          <div className="text-xs text-neutral-400">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </div>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          {/* Time Period Selector */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-neutral-400">Period:</span>
            <div className="flex bg-neutral-700 rounded-lg p-1">
              {(['1W', '2W', '1M'] as TimePeriod[]).map(period => (
                <button
                  key={period}
                  onClick={() => setSelectedPeriod(period)}
                  className={`px-3 py-1 text-xs rounded transition-colors ${
                    selectedPeriod === period
                      ? 'bg-blue-600 text-white'
                      : 'text-neutral-300 hover:text-white'
                  }`}
                >
                  {period}
                </button>
              ))}
            </div>
          </div>

          {/* Display Options */}
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2 text-sm text-neutral-400">
              <input
                type="checkbox"
                checked={showPredictions}
                onChange={e => setShowPredictions(e.target.checked)}
                className="rounded"
              />
              <span>Predictions</span>
            </label>
            <label className="flex items-center space-x-2 text-sm text-neutral-400">
              <input
                type="checkbox"
                checked={showConfidenceInterval}
                onChange={e => setShowConfidenceInterval(e.target.checked)}
                className="rounded"
              />
              <span>Confidence Bands</span>
            </label>
          </div>
        </div>

        {/* Pair Selector */}
        <div className="mb-4">
          <div className="flex flex-wrap gap-2">
            {uniquePairs.map(pair => (
              <button
                key={pair}
                onClick={() => {
                  setSelectedPairs(prev =>
                    prev.includes(pair) ? prev.filter(p => p !== pair) : [...prev, pair]
                  );
                }}
                className={`px-3 py-1 text-xs rounded border transition-colors ${
                  selectedPairs.includes(pair)
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'bg-neutral-700 border-neutral-600 text-neutral-300 hover:bg-neutral-600'
                }`}
              >
                {pair}
              </button>
            ))}
          </div>
        </div>

        {/* Market Regime Indicator */}
        {regimeData && (
          <div className="mb-4 p-3 bg-neutral-700 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="text-sm text-neutral-400">Market Regime:</span>
                <span
                  className={`text-sm font-medium ${
                    regimeData.regime === 'crisis'
                      ? 'text-red-400'
                      : regimeData.regime === 'high_volatility'
                      ? 'text-orange-400'
                      : regimeData.regime === 'low_volatility'
                      ? 'text-green-400'
                      : 'text-blue-400'
                  }`}
                >
                  {regimeData.regime.replace('_', ' ').toUpperCase()}
                </span>
              </div>
              <div className="text-xs text-neutral-400">
                Avg Correlation: {regimeData.characteristics.avg_correlation.toFixed(3)}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="h-80 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="time_display"
              stroke="#9ca3af"
              fontSize={12}
              tickFormatter={(value: any) => {
                const date = new Date(value);
                return selectedPeriod === '1M'
                  ? date.toLocaleDateString()
                  : date.toLocaleDateString() +
                      ' ' +
                      date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
              }}
            />
            <YAxis
              stroke="#9ca3af"
              fontSize={12}
              domain={[-1, 1]}
              tickFormatter={(value: any) => (value as number).toFixed(2)}
            />

            {/* Reference lines for breach thresholds */}
            <ReferenceLine
              y={0.4}
              stroke="#ef4444"
              strokeDasharray="5 5"
              label="Breach Threshold"
            />
            <ReferenceLine y={-0.4} stroke="#ef4444" strokeDasharray="5 5" />
            <ReferenceLine y={0} stroke="#6b7280" strokeWidth={1} />

            <Tooltip content={<CustomTooltip />} />
            <Legend />

            {/* Correlation lines */}
            {selectedPairs.map((pair, index) => (
              <Line
                key={pair}
                type="monotone"
                dataKey={pair}
                stroke={getColorForPair(pair, index)}
                strokeWidth={2}
                dot={false}
                connectNulls={false}
              />
            ))}

            {/* Prediction lines */}
            {showPredictions &&
              selectedPairs.map((pair, index) => (
                <Line
                  key={`${pair}_predicted`}
                  type="monotone"
                  dataKey={`${pair}_predicted`}
                  stroke={getColorForPair(pair, index)}
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  dot={false}
                  connectNulls={false}
                />
              ))}

            <Brush dataKey="time_display" height={30} stroke="#6b7280" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Alerts and Analysis */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Breach Risk Alerts */}
        <div className="bg-neutral-700 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-white mb-3">Breach Risk Analysis</h4>
          <div className="space-y-2">
            {forecastData
              .filter(f => f.breach_probability > 0.1)
              .sort((a, b) => b.breach_probability - a.breach_probability)
              .slice(0, 3)
              .map(forecast => (
                <div key={forecast.pair} className="flex items-center justify-between">
                  <span className="text-sm text-neutral-300">{forecast.pair}</span>
                  <div className="flex items-center space-x-2">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        forecast.breach_probability > 0.5
                          ? 'bg-red-500'
                          : forecast.breach_probability > 0.3
                          ? 'bg-orange-500'
                          : 'bg-yellow-500'
                      }`}
                    />
                    <span className="text-xs text-neutral-400">
                      {(forecast.breach_probability * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            {forecastData.filter(f => f.breach_probability > 0.1).length === 0 && (
              <div className="text-sm text-green-400">No high-risk pairs detected</div>
            )}
          </div>
        </div>

        {/* Trend Summary */}
        <div className="bg-neutral-700 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-white mb-3">Trend Summary</h4>
          <div className="space-y-2">
            {['increasing', 'decreasing', 'stable'].map(direction => {
              const count = trendsData.filter(
                d => d.trend_direction === direction && selectedPairs.includes(d.pair)
              ).length;

              return (
                <div key={direction} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">{getTrendIcon(direction)}</span>
                    <span className="text-sm text-neutral-300 capitalize">{direction}</span>
                  </div>
                  <span className="text-sm text-neutral-400">{count}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

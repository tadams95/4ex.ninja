'use client';

import { useCallback, useMemo, useRef, useState } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useVaRHistory, VaRHistoryPoint } from '../../hooks/useRiskData';

interface VaRTrendChartProps {
  refreshInterval?: number;
}

type TimePeriod = '1D' | '1W' | '1M';
type VaRMethod = 'parametric' | 'historical' | 'monte_carlo';

export default function VaRTrendChart({ refreshInterval = 300000 }: VaRTrendChartProps) {
  const [selectedPeriod, setSelectedPeriod] = useState<TimePeriod>('1D');
  const [selectedMethod, setSelectedMethod] = useState<VaRMethod>('parametric');

  // Accessibility refs
  const chartRef = useRef<HTMLDivElement>(null);
  const periodButtonsRef = useRef<(HTMLButtonElement | null)[]>([]);
  const methodButtonsRef = useRef<(HTMLButtonElement | null)[]>([]);

  const { historyData, loading, error, lastUpdate, refetch } = useVaRHistory(
    selectedPeriod,
    refreshInterval
  );

  const TARGET_VAR_PERCENT = 0.31; // 0.31% target
  const TARGET_VAR_DECIMAL = 0.0031; // As decimal

  // Keyboard navigation for period buttons
  const handlePeriodKeyDown = useCallback(
    (event: React.KeyboardEvent, period: TimePeriod, index: number) => {
      const periods: TimePeriod[] = ['1D', '1W', '1M'];

      switch (event.key) {
        case 'ArrowLeft':
          event.preventDefault();
          const prevIndex = index > 0 ? index - 1 : periods.length - 1;
          periodButtonsRef.current[prevIndex]?.focus();
          break;
        case 'ArrowRight':
          event.preventDefault();
          const nextIndex = index < periods.length - 1 ? index + 1 : 0;
          periodButtonsRef.current[nextIndex]?.focus();
          break;
        case 'Enter':
        case ' ':
          event.preventDefault();
          handlePeriodChange(period);
          break;
      }
    },
    []
  );

  // Keyboard navigation for method buttons
  const handleMethodKeyDown = useCallback(
    (event: React.KeyboardEvent, method: VaRMethod, index: number) => {
      const methods: VaRMethod[] = ['parametric', 'historical', 'monte_carlo'];

      switch (event.key) {
        case 'ArrowLeft':
          event.preventDefault();
          const prevIndex = index > 0 ? index - 1 : methods.length - 1;
          methodButtonsRef.current[prevIndex]?.focus();
          break;
        case 'ArrowRight':
          event.preventDefault();
          const nextIndex = index < methods.length - 1 ? index + 1 : 0;
          methodButtonsRef.current[nextIndex]?.focus();
          break;
        case 'Enter':
        case ' ':
          event.preventDefault();
          handleMethodChange(method);
          break;
      }
    },
    []
  );

  // Optimized period selector with useCallback to prevent unnecessary re-renders
  const handlePeriodChange = useCallback((period: TimePeriod) => {
    setSelectedPeriod(period);
  }, []);

  // Optimized method selector with useCallback
  const handleMethodChange = useCallback((method: VaRMethod) => {
    setSelectedMethod(method);
  }, []);

  // Process data for chart display
  const chartData = useMemo(() => {
    if (!historyData?.data) return [];

    return historyData.data.map((point: VaRHistoryPoint) => {
      const timestamp = new Date(point.timestamp);

      // Format timestamp based on period
      let timeLabel = '';
      if (selectedPeriod === '1D') {
        timeLabel = timestamp.toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
          hour12: false,
        });
      } else if (selectedPeriod === '1W') {
        timeLabel = timestamp.toLocaleDateString('en-US', {
          weekday: 'short',
          month: 'short',
          day: 'numeric',
        });
      } else {
        timeLabel = timestamp.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
        });
      }

      return {
        ...point,
        timeLabel,
        timestamp: timestamp.getTime(),
        // Convert to percentage for display
        parametricPercent: point.parametric * 100,
        historicalPercent: point.historical * 100,
        monteCarloPercent: point.monte_carlo * 100,
        targetPercent: TARGET_VAR_PERCENT,
        isBreach: point[selectedMethod] > TARGET_VAR_DECIMAL,
      };
    });
  }, [historyData, selectedPeriod, selectedMethod]);

  // Calculate breach areas for highlighting
  const breachAreas = useMemo(() => {
    const areas: Array<{ start: number; end: number }> = [];
    let currentBreach: { start: number; end: number } | null = null;

    chartData.forEach((point, index) => {
      if (point.isBreach) {
        if (!currentBreach) {
          currentBreach = { start: index, end: index };
        } else {
          currentBreach.end = index;
        }
      } else {
        if (currentBreach) {
          areas.push(currentBreach);
          currentBreach = null;
        }
      }
    });

    // Don't forget the last breach if it goes to the end
    if (currentBreach) {
      areas.push(currentBreach);
    }

    return areas;
  }, [chartData]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div
          className="bg-neutral-800 border border-neutral-600 rounded-lg p-3 shadow-lg"
          role="tooltip"
          aria-live="polite"
          aria-label={`VaR data for ${data.timeLabel}`}
        >
          <p className="text-neutral-300 text-sm mb-2" id="tooltip-time">
            {data.timeLabel}
          </p>
          <div className="space-y-1" role="list" aria-labelledby="tooltip-time">
            <p
              className="text-blue-400 text-sm"
              role="listitem"
              aria-label={`Parametric VaR: ${data.parametricPercent.toFixed(3)} percent`}
            >
              Parametric VaR: {data.parametricPercent.toFixed(3)}%
            </p>
            <p
              className="text-green-400 text-sm"
              role="listitem"
              aria-label={`Historical VaR: ${data.historicalPercent.toFixed(3)} percent`}
            >
              Historical VaR: {data.historicalPercent.toFixed(3)}%
            </p>
            <p
              className="text-purple-400 text-sm"
              role="listitem"
              aria-label={`Monte Carlo VaR: ${data.monteCarloPercent.toFixed(3)} percent`}
            >
              Monte Carlo VaR: {data.monteCarloPercent.toFixed(3)}%
            </p>
            <p
              className="text-red-400 text-sm border-t border-neutral-600 pt-1 mt-1"
              role="listitem"
              aria-label={`Target VaR: ${TARGET_VAR_PERCENT} percent`}
            >
              Target: {TARGET_VAR_PERCENT}%
            </p>
            {data.isBreach && (
              <p
                className="text-red-500 text-xs font-semibold"
                role="alert"
                aria-label="Breach detected: VaR target exceeded"
              >
                ⚠️ BREACH DETECTED
              </p>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div
        className="bg-neutral-900 border border-neutral-700 rounded-lg p-6"
        role="region"
        aria-label="VaR Trend Chart Loading"
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-white">VaR Trend Analysis</h3>
            <p className="text-sm text-neutral-400">Loading historical data...</p>
          </div>
          <div
            className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-400"
            aria-label="Loading"
          ></div>
        </div>

        {/* Enhanced skeleton with better animations */}
        <div className="space-y-4 mb-6">
          <div className="flex space-x-2">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-8 w-16 bg-neutral-800 rounded animate-pulse"></div>
            ))}
          </div>
          <div className="flex space-x-2">
            {[1, 2, 3].map(i => (
              <div
                key={i}
                className="h-8 w-20 bg-neutral-800 rounded animate-pulse"
                style={{ animationDelay: `${i * 100}ms` }}
              ></div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4 mb-6">
          {[1, 2, 3, 4].map(i => (
            <div
              key={i}
              className="bg-neutral-800 rounded p-3 animate-pulse"
              style={{ animationDelay: `${i * 150}ms` }}
            >
              <div className="h-3 bg-neutral-700 rounded mb-2"></div>
              <div className="h-6 bg-neutral-700 rounded"></div>
            </div>
          ))}
        </div>

        <div className="h-64 bg-neutral-800 rounded animate-pulse"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-neutral-900 border border-red-500 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-red-400">VaR Trend Analysis - Error</h3>
          <button
            onClick={refetch}
            className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
          >
            Retry
          </button>
        </div>
        <p className="text-red-300">Error: {error}</p>
      </div>
    );
  }

  return (
    <div
      className="bg-neutral-900 border border-neutral-700 rounded-lg p-6"
      role="region"
      aria-label="VaR Trend Analysis Dashboard"
      ref={chartRef}
    >
      {/* Header with controls */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white">VaR Trend Analysis</h3>
          <p className="text-sm text-neutral-400">
            Historical Value at Risk ({TARGET_VAR_PERCENT}% target)
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={refetch}
            className="px-3 py-1 bg-neutral-700 text-neutral-300 rounded hover:bg-neutral-600 text-sm"
          >
            ↻ Refresh
          </button>
          <span className="text-xs text-neutral-500">
            Updated: {lastUpdate.toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* Time Period Selector */}
      <div
        className="flex items-center space-x-4 mb-4"
        role="radiogroup"
        aria-label="Select time period for VaR analysis"
      >
        <span className="text-sm text-neutral-400" id="period-label">
          Period:
        </span>
        {(['1D', '1W', '1M'] as TimePeriod[]).map((period, index) => (
          <button
            key={period}
            ref={el => {
              periodButtonsRef.current[index] = el;
            }}
            onClick={() => handlePeriodChange(period)}
            onKeyDown={e => handlePeriodKeyDown(e, period, index)}
            role="radio"
            aria-checked={selectedPeriod === period}
            aria-labelledby="period-label"
            aria-label={`${
              period === '1D' ? 'One day' : period === '1W' ? 'One week' : 'One month'
            } time period`}
            tabIndex={selectedPeriod === period ? 0 : -1}
            className={`px-3 py-1 rounded text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-neutral-900 ${
              selectedPeriod === period
                ? 'bg-blue-600 text-white'
                : 'bg-neutral-700 text-neutral-300 hover:bg-neutral-600'
            }`}
          >
            {period}
          </button>
        ))}
      </div>

      {/* VaR Method Selector */}
      <div
        className="flex items-center space-x-4 mb-6"
        role="radiogroup"
        aria-label="Select VaR calculation method"
      >
        <span className="text-sm text-neutral-400" id="method-label">
          Method:
        </span>
        {(
          [
            { key: 'parametric', label: 'Parametric', color: 'text-blue-400' },
            { key: 'historical', label: 'Historical', color: 'text-green-400' },
            { key: 'monte_carlo', label: 'Monte Carlo', color: 'text-purple-400' },
          ] as const
        ).map((method, index) => (
          <button
            key={method.key}
            ref={el => {
              methodButtonsRef.current[index] = el;
            }}
            onClick={() => handleMethodChange(method.key)}
            onKeyDown={e => handleMethodKeyDown(e, method.key, index)}
            role="radio"
            aria-checked={selectedMethod === method.key}
            aria-labelledby="method-label"
            aria-label={`${method.label} VaR calculation method`}
            tabIndex={selectedMethod === method.key ? 0 : -1}
            className={`px-3 py-1 rounded text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-neutral-900 ${
              selectedMethod === method.key
                ? 'bg-neutral-600 border border-neutral-500'
                : 'bg-neutral-700 hover:bg-neutral-600'
            } ${method.color}`}
          >
            {method.label}
          </button>
        ))}
      </div>

      {/* Summary Stats */}
      {historyData && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-neutral-800 rounded p-3">
            <p className="text-xs text-neutral-400">Total Points</p>
            <p className="text-lg font-semibold text-white">{historyData.summary.total_points}</p>
          </div>
          <div className="bg-neutral-800 rounded p-3">
            <p className="text-xs text-neutral-400">Breaches</p>
            <p className="text-lg font-semibold text-red-400">
              {historyData.summary.breaches_count}
            </p>
          </div>
          <div className="bg-neutral-800 rounded p-3">
            <p className="text-xs text-neutral-400">Avg VaR</p>
            <p className="text-lg font-semibold text-white">
              {(historyData.summary.avg_var * 100).toFixed(3)}%
            </p>
          </div>
          <div className="bg-neutral-800 rounded p-3">
            <p className="text-xs text-neutral-400">Max VaR</p>
            <p className="text-lg font-semibold text-yellow-400">
              {(historyData.summary.max_var * 100).toFixed(3)}%
            </p>
          </div>
        </div>
      )}

      {/* Chart */}
      <div
        className="h-64"
        role="img"
        aria-label={`VaR trend chart showing ${selectedMethod} method over ${selectedPeriod} period. Target VaR is ${TARGET_VAR_PERCENT}%. Current data contains ${chartData.length} data points.`}
      >
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            aria-label="VaR trend visualization"
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="timeLabel" stroke="#9CA3AF" fontSize={12} tick={{ fill: '#9CA3AF' }} />
            <YAxis
              stroke="#9CA3AF"
              fontSize={12}
              tick={{ fill: '#9CA3AF' }}
              tickFormatter={value => `${value.toFixed(2)}%`}
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Target line */}
            <ReferenceLine
              y={TARGET_VAR_PERCENT}
              stroke="#EF4444"
              strokeDasharray="5 5"
              strokeWidth={2}
            />

            {/* VaR lines */}
            <Line
              type="monotone"
              dataKey="parametricPercent"
              stroke="#60A5FA"
              strokeWidth={selectedMethod === 'parametric' ? 3 : 1.5}
              dot={false}
              opacity={selectedMethod === 'parametric' ? 1 : 0.6}
            />
            <Line
              type="monotone"
              dataKey="historicalPercent"
              stroke="#34D399"
              strokeWidth={selectedMethod === 'historical' ? 3 : 1.5}
              dot={false}
              opacity={selectedMethod === 'historical' ? 1 : 0.6}
            />
            <Line
              type="monotone"
              dataKey="monteCarloPercent"
              stroke="#A78BFA"
              strokeWidth={selectedMethod === 'monte_carlo' ? 3 : 1.5}
              dot={false}
              opacity={selectedMethod === 'monte_carlo' ? 1 : 0.6}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center space-x-6 mt-4 text-sm">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-0.5 bg-blue-400"></div>
          <span className="text-neutral-300">Parametric VaR</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-0.5 bg-green-400"></div>
          <span className="text-neutral-300">Historical VaR</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-0.5 bg-purple-400"></div>
          <span className="text-neutral-300">Monte Carlo VaR</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-0.5 bg-red-400 border-dashed border-t"></div>
          <span className="text-neutral-300">Target (0.31%)</span>
        </div>
      </div>

      {/* Screen reader summary */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        VaR Trend Chart Summary: Currently showing {selectedMethod} method over {selectedPeriod}{' '}
        period. Chart contains {chartData.length} data points. Latest VaR value:{' '}
        {chartData.length > 0
          ? (() => {
              const lastPoint = chartData[chartData.length - 1];
              const methodMap = {
                parametric: lastPoint?.parametricPercent,
                historical: lastPoint?.historicalPercent,
                monte_carlo: lastPoint?.monteCarloPercent,
              };
              return `${methodMap[selectedMethod]?.toFixed(3)}%`;
            })()
          : 'No data'}
        .
        {chartData.some(d => d.isBreach)
          ? ' Warning: VaR breaches detected in current period.'
          : ' No VaR breaches in current period.'}
      </div>

      {/* Keyboard navigation help */}
      <div className="mt-4 text-xs text-neutral-500 border-t border-neutral-700 pt-2">
        <p>
          Keyboard navigation: Use arrow keys to navigate between period/method controls, Enter or
          Space to select.
        </p>
      </div>
    </div>
  );
}

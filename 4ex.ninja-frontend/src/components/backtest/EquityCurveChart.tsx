'use client';

import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  getEquityCurveData,
  simulateApiDelay,
  type EquityCurveData,
} from '../../lib/backtestDataLoader';

interface EquityPoint {
  date: string;
  equity: number;
  drawdown: number;
}

const API_BASE = 'http://157.230.58.248:8000';

/**
 * Custom Tooltip Component for the Equity Curve
 */
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-neutral-900 border border-neutral-600 rounded-lg p-3 shadow-lg">
        <p className="text-neutral-300 text-sm mb-1">{new Date(label).toLocaleDateString()}</p>
        <p className="text-green-400 text-sm">Equity: ${data.equity.toLocaleString()}</p>
        <p className="text-red-400 text-sm">Drawdown: {(data.drawdown * 100).toFixed(2)}%</p>
      </div>
    );
  }
  return null;
};

/**
 * Equity Curve Chart Component
 *
 * Displays the equity curve over time with drawdown visualization
 * Uses Recharts with dark theme styling
 */
export default function EquityCurveChart() {
  const {
    data: equityData,
    isLoading,
    error,
  } = useQuery<EquityCurveData>({
    queryKey: ['backtest-equity-curves'],
    queryFn: async () => {
      console.log('Loading equity curves from local data');
      await simulateApiDelay();
      return getEquityCurveData();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Process data for chart
  const chartData = useMemo(() => {
    if (!equityData || !equityData.equity_curves) return [];

    // Get the first strategy's data for now (we can enhance later to allow strategy selection)
    const strategies = Object.values(equityData.equity_curves);
    if (strategies.length === 0) return [];

    const strategy = strategies[0] as any;
    const dates = strategy.dates;
    const equityValues = strategy.equity_values;

    if (!dates || !equityValues) return [];

    return dates.map((date: string, index: number) => {
      const equity = equityValues[index];
      const prevEquity = index > 0 ? equityValues[0] : equity;
      const drawdown = prevEquity > 0 ? (equity - prevEquity) / prevEquity : 0;

      return {
        date,
        equity,
        drawdown: drawdown * 100, // Convert to percentage for display
        drawdownFill: drawdown < -0.05 ? drawdown * 100 : null, // Only show significant drawdowns
      };
    });
  }, [equityData]);

  const stats = useMemo(() => {
    if (!equityData || !equityData.equity_curves) return null;

    // Get the first strategy's data for stats
    const strategies = Object.values(equityData.equity_curves);
    if (strategies.length === 0) return null;

    const strategy = strategies[0];
    const firstEquity = strategy.equity_values[0] || equityData.initial_balance;
    const lastEquity = strategy.equity_values[strategy.equity_values.length - 1] || firstEquity;

    // Calculate total return
    const totalReturn = (lastEquity - firstEquity) / firstEquity;

    // Calculate max drawdown
    let maxEquity = firstEquity;
    let maxDrawdown = 0;

    for (const equity of strategy.equity_values) {
      maxEquity = Math.max(maxEquity, equity);
      const drawdown = (equity - maxEquity) / maxEquity;
      maxDrawdown = Math.min(maxDrawdown, drawdown);
    }

    return {
      totalReturn,
      maxDrawdown: Math.abs(maxDrawdown),
      finalEquity: lastEquity,
      initialEquity: firstEquity,
    };
  }, [equityData]);

  if (isLoading) {
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-neutral-700 rounded mb-4 w-32"></div>
          <div className="h-64 bg-neutral-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-red-400 mb-4">Equity Curve</h3>
        <p className="text-neutral-400 text-sm">Error loading equity curve: {error.message}</p>
      </div>
    );
  }

  if (!chartData || chartData.length === 0) {
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-neutral-300 mb-4">Equity Curve</h3>
        <p className="text-neutral-400 text-sm">No equity data available</p>
      </div>
    );
  }

  return (
    <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-white">Equity Curve</h3>
        {stats && (
          <div className="flex space-x-4 text-sm">
            <span className={`${stats.totalReturn > 0 ? 'text-green-400' : 'text-red-400'}`}>
              Total: {(stats.totalReturn * 100).toFixed(1)}%
            </span>
            <span className="text-red-400">Max DD: {(stats.maxDrawdown * 100).toFixed(1)}%</span>
          </div>
        )}
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{
              top: 5,
              right: 30,
              left: 20,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#404040" opacity={0.3} />
            <XAxis
              dataKey="date"
              stroke="#9CA3AF"
              fontSize={12}
              tickFormatter={value => new Date(value).getFullYear().toString()}
            />
            <YAxis
              stroke="#9CA3AF"
              fontSize={12}
              tickFormatter={value => `$${(value / 1000).toFixed(0)}k`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="equity"
              stroke="#10B981"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: '#10B981' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Quick Stats */}
      {stats && (
        <div className="mt-4 pt-4 border-t border-neutral-700">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-neutral-400">Initial Equity:</span>
              <span className="text-white ml-2">${stats.initialEquity.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-neutral-400">Final Equity:</span>
              <span className="text-white ml-2">${stats.finalEquity.toLocaleString()}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

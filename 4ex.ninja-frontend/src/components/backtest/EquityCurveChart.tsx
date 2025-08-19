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
import { mockEquityData, simulateApiDelay } from './mockData';

interface EquityPoint {
  date: string;
  equity: number;
  drawdown: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
  } = useQuery<EquityPoint[]>({
    queryKey: ['backtest-equity-curves'],
    queryFn: async () => {
      try {
        const response = await fetch(`${API_BASE}/api/v1/backtest/page/equity-curves`);
        if (!response.ok) {
          throw new Error(`API not available: ${response.status}`);
        }
        return response.json();
      } catch (error) {
        // Fallback to mock data for development
        console.log('Using mock data for equity curves (API not available)');
        await simulateApiDelay();
        return mockEquityData;
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Process data for chart
  const chartData = useMemo(() => {
    if (!equityData || equityData.length === 0) return [];

    return equityData.map(point => ({
      date: point.date,
      equity: point.equity,
      drawdown: point.drawdown * 100, // Convert to percentage for display
      drawdownFill: point.drawdown < -0.05 ? point.drawdown * 100 : null, // Only show significant drawdowns
    }));
  }, [equityData]);

  const stats = useMemo(() => {
    if (!equityData || equityData.length === 0) return null;

    const firstEquity = equityData[0]?.equity || 0;
    const lastEquity = equityData[equityData.length - 1]?.equity || 0;
    const maxDrawdown = Math.min(...equityData.map(p => p.drawdown));
    const totalReturn = firstEquity > 0 ? (lastEquity - firstEquity) / firstEquity : 0;

    return {
      totalReturn,
      maxDrawdown,
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

'use client';

import { useQuery } from '@tanstack/react-query';
import React, { useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  loadOptimizationResults,
  simulateApiDelay,
  type OptimizationResults,
} from '../../lib/realOptimizationDataLoader';

/**
 * Enhanced Daily EMA Strategy Visual Analytics
 *
 * Professional analytics dashboard showing real optimization results
 * for the Enhanced Daily EMA Strategy across 10 currency pairs
 */
export default function VisualAnalytics() {
  const [selectedChart, setSelectedChart] = useState<string>('');

  const {
    data: optimizationData,
    isLoading,
    error,
  } = useQuery<OptimizationResults>({
    queryKey: ['optimization-results'],
    queryFn: async () => {
      console.log('Loading Enhanced Daily EMA Strategy optimization results');
      await simulateApiDelay();
      return loadOptimizationResults();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-6 bg-neutral-700 rounded mb-4 w-64"></div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <div
                key={i}
                className="h-80 bg-neutral-800 border border-neutral-700 rounded-lg"
              ></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-red-400 mb-4">Visual Analytics</h3>
        <p className="text-neutral-400 text-sm">Error loading optimization data: {error.message}</p>
      </div>
    );
  }

  if (!optimizationData) {
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-neutral-300 mb-4">Visual Analytics</h3>
        <p className="text-neutral-400 text-sm">No optimization data available</p>
      </div>
    );
  }

  const charts = [
    {
      key: 'performance_overview',
      title: 'Performance Overview',
      description: 'All 10 pairs: Profitable vs Unprofitable comparison',
    },
    {
      key: 'jpy_dominance',
      title: 'JPY Dominance Analysis',
      description: 'JPY pairs vs Non-JPY pairs performance',
    },
    {
      key: 'trading_costs_impact',
      title: 'Trading Costs Impact',
      description: 'Gross returns vs Net returns after costs',
    },
    {
      key: 'win_rate_correlation',
      title: 'Win Rate vs Return',
      description: 'Correlation between win rate and annual returns',
    },
    {
      key: 'ema_configuration',
      title: 'EMA Configuration Analysis',
      description: 'Performance by EMA parameter settings',
    },
    {
      key: 'tier_performance',
      title: 'Performance Tiers',
      description: 'Strategy performance by tier classification',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col space-y-4">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-white">Enhanced Daily EMA Strategy Analytics</h2>
            <p className="text-sm text-neutral-400 mt-1">
              Visual analysis of optimization results across{' '}
              {optimizationData.optimization_info.total_pairs_tested} currency pairs
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-neutral-400">Success Rate</div>
            <div className="text-lg font-bold text-green-400">
              {optimizationData.optimization_info.success_rate}
            </div>
          </div>
        </div>

        {/* Key Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-neutral-800 border border-neutral-700 rounded-lg">
          <div className="text-center">
            <div className="text-lg font-bold text-green-400">
              {Object.keys(optimizationData.profitable_pairs).length}
            </div>
            <div className="text-xs text-neutral-400">Profitable Pairs</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-red-400">
              {Object.keys(optimizationData.unprofitable_pairs).length}
            </div>
            <div className="text-xs text-neutral-400">Unprofitable Pairs</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-blue-400">
              {optimizationData.summary_stats.best_return}
            </div>
            <div className="text-xs text-neutral-400">Best Return</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-purple-400">
              {optimizationData.summary_stats.top_performer}
            </div>
            <div className="text-xs text-neutral-400">Top Performer</div>
          </div>
        </div>
      </div>

      {/* Chart Selection */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setSelectedChart('')}
          className={`px-3 py-1 rounded-md text-sm transition-colors ${
            selectedChart === ''
              ? 'bg-blue-600 text-white'
              : 'bg-neutral-700 text-neutral-300 hover:bg-neutral-600'
          }`}
        >
          All Charts
        </button>
        {charts.map(chart => (
          <button
            key={chart.key}
            onClick={() => setSelectedChart(chart.key)}
            className={`px-3 py-1 rounded-md text-sm transition-colors ${
              selectedChart === chart.key
                ? 'bg-blue-600 text-white'
                : 'bg-neutral-700 text-neutral-300 hover:bg-neutral-600'
            }`}
          >
            {chart.title}
          </button>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {charts
          .filter(chart => selectedChart === '' || chart.key === selectedChart)
          .map(chart => (
            <ChartCard key={chart.key} chart={chart} optimizationData={optimizationData} />
          ))}
      </div>
    </div>
  );
}

/**
 * Individual Chart Card Component
 */
interface ChartCardProps {
  chart: {
    key: string;
    title: string;
    description: string;
  };
  optimizationData: OptimizationResults;
}

function ChartCard({ chart, optimizationData }: ChartCardProps) {
  const [showRawData, setShowRawData] = useState(false);

  const renderChart = () => {
    if (showRawData) {
      return (
        <div className="max-h-72 overflow-y-auto">
          <pre className="text-xs text-neutral-300 font-mono">
            {JSON.stringify(optimizationData, null, 2)}
          </pre>
        </div>
      );
    }

    switch (chart.key) {
      case 'performance_overview':
        return <PerformanceOverviewChart data={optimizationData} />;
      case 'jpy_dominance':
        return <JPYDominanceChart data={optimizationData} />;
      case 'trading_costs_impact':
        return <TradingCostsChart data={optimizationData} />;
      case 'win_rate_correlation':
        return <WinRateCorrelationChart data={optimizationData} />;
      case 'ema_configuration':
        return <EMAConfigurationChart data={optimizationData} />;
      case 'tier_performance':
        return <TierPerformanceChart data={optimizationData} />;
      default:
        return <div className="text-neutral-400 text-center py-8">Chart not implemented</div>;
    }
  };

  return (
    <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white mb-2">{chart.title}</h3>
          <p className="text-sm text-neutral-400">{chart.description}</p>
        </div>
        <button
          onClick={() => setShowRawData(!showRawData)}
          className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
        >
          {showRawData ? 'Show Chart' : 'Show Data'}
        </button>
      </div>

      {/* Chart Area */}
      <div className="bg-neutral-900 border border-neutral-600 rounded-lg p-4 h-80">
        {renderChart()}
      </div>
    </div>
  );
}

/**
 * Performance Overview Chart - All 10 pairs comparison
 */
function PerformanceOverviewChart({ data }: { data: OptimizationResults }) {
  const chartData = React.useMemo(() => {
    const profitable = Object.entries(data.profitable_pairs).map(([pair, metrics]) => ({
      pair,
      return: parseFloat(metrics.annual_return.replace('%', '')),
      type: 'Profitable',
      tier: metrics.tier,
    }));

    const unprofitable = Object.entries(data.unprofitable_pairs).map(([pair, metrics]) => ({
      pair,
      return: parseFloat(metrics.annual_return.replace('%', '')),
      type: 'Unprofitable',
      tier: 'UNPROFITABLE',
    }));

    return [...profitable, ...unprofitable].sort((a, b) => b.return - a.return);
  }, [data]);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chartData} margin={{ top: 20, right: 30, bottom: 60, left: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis
          dataKey="pair"
          stroke="#9ca3af"
          fontSize={11}
          angle={-45}
          textAnchor="end"
          height={80}
        />
        <YAxis
          stroke="#9ca3af"
          fontSize={12}
          label={{
            value: 'Annual Return %',
            angle: -90,
            position: 'insideLeft',
            style: { textAnchor: 'middle', fill: '#9ca3af' },
          }}
        />
        <Tooltip
          content={({ active, payload, label }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload;
              return (
                <div className="bg-neutral-800 border border-neutral-600 rounded-lg p-3 shadow-lg">
                  <p className="text-white font-semibold text-sm">{label}</p>
                  <p className={`text-sm ${data.return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    Return: {data.return.toFixed(1)}%
                  </p>
                  <p className="text-neutral-400 text-xs">Type: {data.type}</p>
                  <p className="text-neutral-400 text-xs">Tier: {data.tier}</p>
                </div>
              );
            }
            return null;
          }}
        />
        <Bar dataKey="return">
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.return >= 0 ? '#10b981' : '#ef4444'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/**
 * JPY Dominance Analysis Chart
 */
function JPYDominanceChart({ data }: { data: OptimizationResults }) {
  const chartData = React.useMemo(() => {
    const jpyPairs = Object.entries(data.profitable_pairs)
      .filter(([pair]) => pair.includes('JPY'))
      .map(([pair, metrics]) => ({
        pair,
        return: parseFloat(metrics.annual_return.replace('%', '')),
        category: 'JPY Pairs',
      }));

    const nonJpyPairs = Object.entries(data.profitable_pairs)
      .filter(([pair]) => !pair.includes('JPY'))
      .map(([pair, metrics]) => ({
        pair,
        return: parseFloat(metrics.annual_return.replace('%', '')),
        category: 'Non-JPY Pairs',
      }));

    return [...jpyPairs, ...nonJpyPairs];
  }, [data]);

  const pieData = React.useMemo(() => {
    const jpyCount = chartData.filter(item => item.category === 'JPY Pairs').length;
    const nonJpyCount = chartData.filter(item => item.category === 'Non-JPY Pairs').length;

    return [
      { name: 'JPY Pairs', value: jpyCount, color: '#10b981' },
      { name: 'Non-JPY Pairs', value: nonJpyCount, color: '#3b82f6' },
    ];
  }, [chartData]);

  return (
    <div className="grid grid-cols-2 h-full">
      {/* Pie Chart */}
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={pieData}
            cx="50%"
            cy="50%"
            outerRadius={60}
            fill="#8884d8"
            dataKey="value"
            label={({ name, value }) => `${name}: ${value}`}
          >
            {pieData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>

      {/* Bar Chart */}
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 20, right: 30, bottom: 40, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="pair"
            stroke="#9ca3af"
            fontSize={10}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis stroke="#9ca3af" fontSize={12} />
          <Tooltip />
          <Bar dataKey="return">
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.category === 'JPY Pairs' ? '#10b981' : '#3b82f6'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Trading Costs Impact Chart
 */
function TradingCostsChart({ data }: { data: OptimizationResults }) {
  const chartData = React.useMemo(() => {
    return Object.entries(data.profitable_pairs).map(([pair, metrics]) => ({
      pair,
      gross_return: metrics.gross_return,
      trading_costs: metrics.trading_costs,
      net_return: metrics.net_return,
    }));
  }, [data]);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chartData} margin={{ top: 20, right: 30, bottom: 60, left: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis
          dataKey="pair"
          stroke="#9ca3af"
          fontSize={11}
          angle={-45}
          textAnchor="end"
          height={80}
        />
        <YAxis
          stroke="#9ca3af"
          fontSize={12}
          label={{
            value: 'Return %',
            angle: -90,
            position: 'insideLeft',
            style: { textAnchor: 'middle', fill: '#9ca3af' },
          }}
        />
        <Tooltip
          content={({ active, payload, label }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload;
              return (
                <div className="bg-neutral-800 border border-neutral-600 rounded-lg p-3 shadow-lg">
                  <p className="text-white font-semibold text-sm">{label}</p>
                  <p className="text-green-400 text-xs">Gross: {data.gross_return}%</p>
                  <p className="text-red-400 text-xs">Costs: -{data.trading_costs}%</p>
                  <p className="text-blue-400 text-xs">Net: {data.net_return}%</p>
                </div>
              );
            }
            return null;
          }}
        />
        <Bar dataKey="gross_return" fill="#22c55e" name="Gross Return" />
        <Bar dataKey="net_return" fill="#3b82f6" name="Net Return" />
        <Legend />
      </BarChart>
    </ResponsiveContainer>
  );
}

/**
 * Win Rate vs Return Correlation Chart
 */
function WinRateCorrelationChart({ data }: { data: OptimizationResults }) {
  const chartData = React.useMemo(() => {
    return Object.entries(data.profitable_pairs).map(([pair, metrics]) => ({
      pair,
      win_rate: parseFloat(metrics.win_rate.replace('%', '')),
      annual_return: parseFloat(metrics.annual_return.replace('%', '')),
      tier: metrics.tier,
    }));
  }, [data]);

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'HIGHLY_PROFITABLE':
        return '#10b981';
      case 'PROFITABLE':
        return '#3b82f6';
      case 'MARGINALLY_PROFITABLE':
        return '#f59e0b';
      default:
        return '#6b7280';
    }
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ScatterChart margin={{ top: 20, right: 30, bottom: 60, left: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis
          type="number"
          dataKey="win_rate"
          domain={[30, 80]}
          stroke="#9ca3af"
          fontSize={12}
          label={{
            value: 'Win Rate %',
            position: 'insideBottom',
            offset: -10,
            style: { textAnchor: 'middle', fill: '#9ca3af' },
          }}
        />
        <YAxis
          type="number"
          dataKey="annual_return"
          domain={[0, 16]}
          stroke="#9ca3af"
          fontSize={12}
          label={{
            value: 'Annual Return %',
            angle: -90,
            position: 'insideLeft',
            style: { textAnchor: 'middle', fill: '#9ca3af' },
          }}
        />
        <Tooltip
          content={({ active, payload }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload;
              return (
                <div className="bg-neutral-800 border border-neutral-600 rounded-lg p-3 shadow-lg">
                  <p className="text-white font-semibold text-sm">{data.pair}</p>
                  <p className="text-green-400 text-xs">Return: {data.annual_return}%</p>
                  <p className="text-blue-400 text-xs">Win Rate: {data.win_rate}%</p>
                  <p className="text-neutral-400 text-xs">Tier: {data.tier}</p>
                </div>
              );
            }
            return null;
          }}
        />
        <Scatter data={chartData}>
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={getTierColor(entry.tier)} />
          ))}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  );
}

/**
 * EMA Configuration Analysis Chart
 */
function EMAConfigurationChart({ data }: { data: OptimizationResults }) {
  const chartData = React.useMemo(() => {
    const configCounts: Record<string, { count: number; total_return: number; pairs: string[] }> =
      {};

    Object.entries(data.profitable_pairs).forEach(([pair, metrics]) => {
      const config = metrics.ema_config;
      if (!configCounts[config]) {
        configCounts[config] = { count: 0, total_return: 0, pairs: [] };
      }
      configCounts[config].count++;
      configCounts[config].total_return += parseFloat(metrics.annual_return.replace('%', ''));
      configCounts[config].pairs.push(pair);
    });

    return Object.entries(configCounts).map(([config, data]) => ({
      config,
      count: data.count,
      avg_return: data.total_return / data.count,
      pairs: data.pairs.join(', '),
    }));
  }, [data]);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chartData} margin={{ top: 20, right: 30, bottom: 40, left: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis dataKey="config" stroke="#9ca3af" fontSize={12} />
        <YAxis
          stroke="#9ca3af"
          fontSize={12}
          label={{
            value: 'Average Return %',
            angle: -90,
            position: 'insideLeft',
            style: { textAnchor: 'middle', fill: '#9ca3af' },
          }}
        />
        <Tooltip
          content={({ active, payload, label }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload;
              return (
                <div className="bg-neutral-800 border border-neutral-600 rounded-lg p-3 shadow-lg">
                  <p className="text-white font-semibold text-sm">EMA {label}</p>
                  <p className="text-green-400 text-xs">
                    Avg Return: {data.avg_return.toFixed(1)}%
                  </p>
                  <p className="text-blue-400 text-xs">Pairs: {data.count}</p>
                  <p className="text-neutral-400 text-xs">{data.pairs}</p>
                </div>
              );
            }
            return null;
          }}
        />
        <Bar dataKey="avg_return" fill="#8b5cf6">
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.avg_return > 8 ? '#10b981' : '#8b5cf6'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/**
 * Tier Performance Chart
 */
function TierPerformanceChart({ data }: { data: OptimizationResults }) {
  const chartData = React.useMemo(() => {
    const tiers: Record<string, { count: number; total_return: number; pairs: string[] }> = {};

    Object.entries(data.profitable_pairs).forEach(([pair, metrics]) => {
      const tier = metrics.tier;
      if (!tiers[tier]) {
        tiers[tier] = { count: 0, total_return: 0, pairs: [] };
      }
      tiers[tier].count++;
      tiers[tier].total_return += parseFloat(metrics.annual_return.replace('%', ''));
      tiers[tier].pairs.push(pair);
    });

    return Object.entries(tiers)
      .map(([tier, data]) => ({
        tier: tier.replace(/_/g, ' '),
        count: data.count,
        avg_return: data.total_return / data.count,
        total_return: data.total_return,
        pairs: data.pairs.join(', '),
      }))
      .sort((a, b) => b.avg_return - a.avg_return);
  }, [data]);

  const getTierColor = (tier: string) => {
    if (tier.includes('HIGHLY')) return '#10b981';
    if (tier.includes('PROFITABLE') && !tier.includes('MARGINALLY')) return '#3b82f6';
    if (tier.includes('MARGINALLY')) return '#f59e0b';
    return '#6b7280';
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chartData} margin={{ top: 20, right: 30, bottom: 60, left: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis
          dataKey="tier"
          stroke="#9ca3af"
          fontSize={11}
          angle={-45}
          textAnchor="end"
          height={80}
        />
        <YAxis
          stroke="#9ca3af"
          fontSize={12}
          label={{
            value: 'Average Return %',
            angle: -90,
            position: 'insideLeft',
            style: { textAnchor: 'middle', fill: '#9ca3af' },
          }}
        />
        <Tooltip
          content={({ active, payload, label }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload;
              return (
                <div className="bg-neutral-800 border border-neutral-600 rounded-lg p-3 shadow-lg">
                  <p className="text-white font-semibold text-sm">{label}</p>
                  <p className="text-green-400 text-xs">
                    Avg Return: {data.avg_return.toFixed(1)}%
                  </p>
                  <p className="text-blue-400 text-xs">Pairs: {data.count}</p>
                  <p className="text-purple-400 text-xs">
                    Total Return: {data.total_return.toFixed(1)}%
                  </p>
                  <p className="text-neutral-400 text-xs">{data.pairs}</p>
                </div>
              );
            }
            return null;
          }}
        />
        <Bar dataKey="avg_return">
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={getTierColor(entry.tier)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

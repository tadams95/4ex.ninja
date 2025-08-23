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
  getConfidenceAnalysis,
  loadEnhancedOptimizationResults,
  simulateApiDelay,
  type ConfidenceAnalysis,
  type EnhancedOptimizationResults,
} from '../../lib/secondBacktestDataLoader';

/**
 * ENHANCED Visual Analytics Component v2.0
 *
 * Professional analytics dashboard showing SECOND BACKTEST results
 * Features: ALL 10 pairs profitable, 4,436 total trades
 * Data Source: Enhanced Daily Strategy v2.0 - August 21, 2025
 */
export default function VisualAnalytics() {
  const [selectedChart, setSelectedChart] = useState<string>('');

  const {
    data: optimizationData,
    isLoading,
    error,
  } = useQuery<EnhancedOptimizationResults>({
    queryKey: ['enhanced-optimization-results-v2'],
    queryFn: async () => {
      console.log('Loading Enhanced Daily Strategy v2.0 optimization results for analytics');
      await simulateApiDelay();
      return loadEnhancedOptimizationResults();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const {
    data: confidenceData,
    isLoading: isLoadingConfidence,
    error: confidenceError,
  } = useQuery<ConfidenceAnalysis | null>({
    queryKey: ['confidence-analysis-v2'],
    queryFn: async () => {
      console.log('Loading confidence analysis for visual analytics');
      await simulateApiDelay();
      return getConfidenceAnalysis();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const isLoadingAll = isLoading || isLoadingConfidence;
  const errorAll = error || confidenceError;

  if (isLoadingAll) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-6 bg-neutral-700 rounded mb-4 w-64"></div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
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

  if (errorAll) {
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-red-400 mb-4">Enhanced Visual Analytics v2.0</h3>
        <p className="text-neutral-400 text-sm">Error loading analytics data: {errorAll.message}</p>
      </div>
    );
  }

  if (!optimizationData) {
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-neutral-300 mb-4">
          Enhanced Visual Analytics v2.0
        </h3>
        <p className="text-neutral-400 text-sm">No optimization data available</p>
      </div>
    );
  }

  const charts = [
    {
      key: 'performance_overview',
      title: 'Performance Overview',
      description: 'ALL 10 pairs profitable - Enhanced v2.0 breakthrough',
    },
    {
      key: 'profit_factor_analysis',
      title: 'Profit Factor Analysis',
      description: 'Profit factors for all 10 pairs (3.1x - 4.14x range)',
    },
    {
      key: 'trade_frequency_performance',
      title: 'Trade Frequency vs Performance',
      description: 'Total trades vs returns scatter plot analysis',
    },
    {
      key: 'confidence_vs_backtest',
      title: 'Confidence vs Backtest Results',
      description: 'Backtest results vs realistic live trading expectations',
    },
    {
      key: 'win_rate_distribution',
      title: 'Win Rate Distribution',
      description: 'Win rate histogram (59.7% - 68.0% range)',
    },
    {
      key: 'max_consecutive_losses',
      title: 'Max Consecutive Losses',
      description: 'Risk analysis of maximum consecutive losses per pair',
    },
    {
      key: 'jpy_dominance',
      title: 'JPY Dominance Analysis',
      description: 'JPY pairs vs Non-JPY pairs performance comparison',
    },
    {
      key: 'tier_performance',
      title: 'Performance Tiers',
      description: 'Gold/Silver/Bronze tier classification analysis',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col space-y-4">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-white">🚀 Enhanced Visual Analytics v2.0</h2>
            <p className="text-sm text-neutral-400 mt-1">
              Comprehensive analysis of Enhanced Daily Strategy v2.0 - ALL{' '}
              {optimizationData.optimization_info.total_pairs_tested} pairs profitable!
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-neutral-400">Success Rate</div>
            <div className="text-lg font-bold text-green-400">100% - Breakthrough Result!</div>
          </div>
        </div>

        {/* Enhanced Key Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gradient-to-r from-green-900/30 to-blue-900/30 border border-green-700/50 rounded-lg">
          <div className="text-center">
            <div className="text-lg font-bold text-green-400">
              {Object.keys(optimizationData.profitable_pairs).length}
            </div>
            <div className="text-xs text-green-300">ALL Profitable</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-blue-400">
              {optimizationData.optimization_info.total_trades.toLocaleString()}
            </div>
            <div className="text-xs text-blue-300">Total Trades</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-purple-400">3.1x - 4.14x</div>
            <div className="text-xs text-purple-300">Profit Factor Range</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-yellow-400">USD_JPY</div>
            <div className="text-xs text-yellow-300">Top Performer</div>
          </div>
        </div>

        {/* Confidence Analysis Warning */}
        {confidenceData && (
          <div className="p-4 bg-yellow-900/20 border border-yellow-700 rounded-lg">
            <p className="text-yellow-400 text-sm font-medium">
              ⚠️ Live Trading Reality Check: While backtest shows exceptional results, confidence
              analysis suggests{' '}
              {confidenceData?.realistic_projections?.live_trading_expectations?.win_rate_range
                ? `${confidenceData.realistic_projections.live_trading_expectations.win_rate_range.min}-${confidenceData.realistic_projections.live_trading_expectations.win_rate_range.max}%`
                : '48-52%'}{' '}
              win rates in live trading due to spreads, slippage, and market conditions.
            </p>
          </div>
        )}
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
            <ChartCard
              key={chart.key}
              chart={chart}
              optimizationData={optimizationData}
              confidenceData={confidenceData || null}
            />
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
  optimizationData: EnhancedOptimizationResults;
  confidenceData: ConfidenceAnalysis | null;
}

function ChartCard({ chart, optimizationData, confidenceData }: ChartCardProps) {
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
        return <PerformanceOverviewChart data={optimizationData} confidenceData={confidenceData} />;
      case 'profit_factor_analysis':
        return <ProfitFactorAnalysisChart data={optimizationData} />;
      case 'trade_frequency_performance':
        return <TradeFrequencyPerformanceChart data={optimizationData} />;
      case 'confidence_vs_backtest':
        return (
          <ConfidenceVsBacktestChart data={optimizationData} confidenceData={confidenceData} />
        );
      case 'win_rate_distribution':
        return <WinRateDistributionChart data={optimizationData} />;
      case 'max_consecutive_losses':
        return <MaxConsecutiveLossesChart data={optimizationData} />;
      case 'jpy_dominance':
        return <JPYDominanceChart data={optimizationData} />;
      case 'tier_performance':
        return <TierPerformanceChart data={optimizationData} />;
      default:
        return (
          <div className="text-neutral-400 text-center py-8">
            <p>Chart: {chart.key}</p>
            <p className="text-sm">Enhanced chart implementation available</p>
          </div>
        );
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
 * Performance Overview Chart - ALL 10 pairs comparison (Enhanced v2.0)
 */
function PerformanceOverviewChart({
  data,
  confidenceData,
}: {
  data: EnhancedOptimizationResults;
  confidenceData?: ConfidenceAnalysis | null;
}) {
  const chartData = React.useMemo(() => {
    const profitable = Object.entries(data.profitable_pairs).map(([pair, metrics]) => ({
      pair,
      return: parseFloat(metrics.annual_return.replace('%', '')),
      type: 'Profitable',
      tier: metrics.tier,
      total_trades: metrics.total_trades,
      profit_factor: metrics.profit_factor,
    }));

    return profitable.sort((a, b) => b.return - a.return);
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
                  <p className="text-green-400 text-sm">Return: {data.return.toFixed(1)}%</p>
                  <p className="text-blue-400 text-xs">Trades: {data.total_trades}</p>
                  <p className="text-purple-400 text-xs">PF: {data.profit_factor?.toFixed(2)}x</p>
                  <p className="text-neutral-400 text-xs">Tier: {data.tier}</p>
                </div>
              );
            }
            return null;
          }}
        />
        <Bar dataKey="return">
          {chartData.map((entry, index) => {
            const tierColor =
              entry.tier === 'GOLD_TIER'
                ? '#fbbf24'
                : entry.tier === 'SILVER_TIER'
                ? '#d1d5db'
                : '#fb923c';
            return <Cell key={`cell-${index}`} fill={tierColor} />;
          })}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/**
 * NEW: Profit Factor Analysis Chart - All 10 pairs (3.1x - 4.14x range)
 */
function ProfitFactorAnalysisChart({ data }: { data: EnhancedOptimizationResults }) {
  const chartData = React.useMemo(() => {
    return Object.entries(data.profitable_pairs)
      .map(([pair, metrics]) => ({
        pair,
        profit_factor: metrics.profit_factor,
        total_trades: metrics.total_trades,
        tier: metrics.tier,
      }))
      .sort((a, b) => b.profit_factor - a.profit_factor);
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
            value: 'Profit Factor',
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
                  <p className="text-green-400 text-sm">PF: {data.profit_factor.toFixed(2)}x</p>
                  <p className="text-blue-400 text-xs">Trades: {data.total_trades}</p>
                  <p className="text-neutral-400 text-xs">Tier: {data.tier}</p>
                </div>
              );
            }
            return null;
          }}
        />
        <Bar dataKey="profit_factor">
          {chartData.map((entry, index) => {
            const tierColor =
              entry.tier === 'GOLD_TIER'
                ? '#fbbf24'
                : entry.tier === 'SILVER_TIER'
                ? '#d1d5db'
                : '#fb923c';
            return <Cell key={`cell-${index}`} fill={tierColor} />;
          })}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/**
 * NEW: Trade Frequency vs Performance Scatter Plot
 */
function TradeFrequencyPerformanceChart({ data }: { data: EnhancedOptimizationResults }) {
  const chartData = React.useMemo(() => {
    return Object.entries(data.profitable_pairs).map(([pair, metrics]) => ({
      pair,
      total_trades: metrics.total_trades,
      annual_return: parseFloat(metrics.annual_return.replace('%', '')),
      profit_factor: metrics.profit_factor,
      tier: metrics.tier,
    }));
  }, [data]);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ScatterChart margin={{ top: 20, right: 30, bottom: 60, left: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis
          type="number"
          dataKey="total_trades"
          domain={[300, 550]}
          stroke="#9ca3af"
          fontSize={12}
          label={{
            value: 'Total Trades',
            position: 'insideBottom',
            offset: -10,
            style: { textAnchor: 'middle', fill: '#9ca3af' },
          }}
        />
        <YAxis
          type="number"
          dataKey="annual_return"
          domain={[8, 20]}
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
                  <p className="text-blue-400 text-xs">Trades: {data.total_trades}</p>
                  <p className="text-purple-400 text-xs">PF: {data.profit_factor.toFixed(2)}x</p>
                  <p className="text-neutral-400 text-xs">Tier: {data.tier}</p>
                </div>
              );
            }
            return null;
          }}
        />
        <Scatter data={chartData}>
          {chartData.map((entry, index) => {
            const tierColor =
              entry.tier === 'GOLD_TIER'
                ? '#fbbf24'
                : entry.tier === 'SILVER_TIER'
                ? '#d1d5db'
                : '#fb923c';
            return <Cell key={`cell-${index}`} fill={tierColor} />;
          })}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  );
}

/**
 * NEW: Confidence vs Backtest Results Comparison
 */
function ConfidenceVsBacktestChart({
  data,
  confidenceData,
}: {
  data: EnhancedOptimizationResults;
  confidenceData?: ConfidenceAnalysis | null;
}) {
  const chartData = React.useMemo(() => {
    const pairs = Object.entries(data.profitable_pairs);

    return pairs.map(([pair, metrics]) => ({
      pair,
      backtest_wr: parseFloat(metrics.win_rate.replace('%', '')),
      live_wr_estimate: 50, // Estimated live trading win rate
      backtest_pf: metrics.profit_factor,
      live_pf_estimate: metrics.profit_factor * 0.6, // Estimated 40% reduction
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
            value: 'Win Rate %',
            angle: -90,
            position: 'insideLeft',
            style: { textAnchor: 'middle', fill: '#9ca3af' },
          }}
        />
        <Tooltip
          content={({ active, payload, label }) => {
            if (active && payload && payload.length) {
              return (
                <div className="bg-neutral-800 border border-neutral-600 rounded-lg p-3 shadow-lg">
                  <p className="text-white font-semibold text-sm">{label}</p>
                  <p className="text-green-400 text-xs">Backtest WR: {payload[0]?.value}%</p>
                  <p className="text-yellow-400 text-xs">Live Est. WR: {payload[1]?.value}%</p>
                </div>
              );
            }
            return null;
          }}
        />
        <Bar dataKey="backtest_wr" fill="#10b981" name="Backtest Win Rate" />
        <Bar dataKey="live_wr_estimate" fill="#f59e0b" name="Live Trading Estimate" />
        <Legend />
      </BarChart>
    </ResponsiveContainer>
  );
}

/**
 * NEW: Win Rate Distribution Histogram (59.7% - 68.0% range)
 */
function WinRateDistributionChart({ data }: { data: EnhancedOptimizationResults }) {
  const chartData = React.useMemo(() => {
    const winRates = Object.entries(data.profitable_pairs).map(([_, metrics]) =>
      parseFloat(metrics.win_rate.replace('%', ''))
    );

    // Create histogram bins
    const bins = [
      { range: '59-61%', count: 0, min: 59, max: 61 },
      { range: '61-63%', count: 0, min: 61, max: 63 },
      { range: '63-65%', count: 0, min: 63, max: 65 },
      { range: '65-67%', count: 0, min: 65, max: 67 },
      { range: '67-69%', count: 0, min: 67, max: 69 },
    ];

    winRates.forEach(wr => {
      bins.forEach(bin => {
        if (wr >= bin.min && wr < bin.max) {
          bin.count++;
        }
      });
    });

    return bins;
  }, [data]);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chartData} margin={{ top: 20, right: 30, bottom: 40, left: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis dataKey="range" stroke="#9ca3af" fontSize={12} />
        <YAxis
          stroke="#9ca3af"
          fontSize={12}
          label={{
            value: 'Number of Pairs',
            angle: -90,
            position: 'insideLeft',
            style: { textAnchor: 'middle', fill: '#9ca3af' },
          }}
        />
        <Tooltip
          content={({ active, payload, label }) => {
            if (active && payload && payload.length) {
              return (
                <div className="bg-neutral-800 border border-neutral-600 rounded-lg p-3 shadow-lg">
                  <p className="text-white font-semibold text-sm">Win Rate: {label}</p>
                  <p className="text-blue-400 text-xs">Pairs: {payload[0]?.value}</p>
                </div>
              );
            }
            return null;
          }}
        />
        <Bar dataKey="count" fill="#3b82f6" />
      </BarChart>
    </ResponsiveContainer>
  );
}

/**
 * NEW: Max Consecutive Losses Risk Analysis
 */
function MaxConsecutiveLossesChart({ data }: { data: EnhancedOptimizationResults }) {
  const chartData = React.useMemo(() => {
    return Object.entries(data.profitable_pairs)
      .map(([pair, metrics]) => ({
        pair,
        max_consecutive_losses: metrics.max_consecutive_losses,
        total_trades: metrics.total_trades,
        win_rate: parseFloat(metrics.win_rate.replace('%', '')),
        tier: metrics.tier,
      }))
      .sort((a, b) => b.max_consecutive_losses - a.max_consecutive_losses);
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
            value: 'Max Consecutive Losses',
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
                  <p className="text-red-400 text-sm">Max Losses: {data.max_consecutive_losses}</p>
                  <p className="text-green-400 text-xs">Win Rate: {data.win_rate}%</p>
                  <p className="text-blue-400 text-xs">Total Trades: {data.total_trades}</p>
                  <p className="text-neutral-400 text-xs">Tier: {data.tier}</p>
                </div>
              );
            }
            return null;
          }}
        />
        <Bar dataKey="max_consecutive_losses">
          {chartData.map((entry, index) => {
            // Color by risk level
            const riskColor =
              entry.max_consecutive_losses <= 5
                ? '#10b981' // Low risk - green
                : entry.max_consecutive_losses <= 8
                ? '#f59e0b' // Medium risk - yellow
                : '#ef4444'; // High risk - red
            return <Cell key={`cell-${index}`} fill={riskColor} />;
          })}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/**
 * JPY Dominance Analysis Chart (Enhanced v2.0)
 */
function JPYDominanceChart({ data }: { data: EnhancedOptimizationResults }) {
  const chartData = React.useMemo(() => {
    const jpyPairs = Object.entries(data.profitable_pairs)
      .filter(([pair]) => pair.includes('JPY'))
      .map(([pair, metrics]) => ({
        pair,
        return: parseFloat(metrics.annual_return.replace('%', '')),
        category: 'JPY Pairs',
        profit_factor: metrics.profit_factor,
      }));

    const nonJpyPairs = Object.entries(data.profitable_pairs)
      .filter(([pair]) => !pair.includes('JPY'))
      .map(([pair, metrics]) => ({
        pair,
        return: parseFloat(metrics.annual_return.replace('%', '')),
        category: 'Non-JPY Pairs',
        profit_factor: metrics.profit_factor,
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
 * Tier Performance Chart (Enhanced v2.0)
 */
function TierPerformanceChart({ data }: { data: EnhancedOptimizationResults }) {
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

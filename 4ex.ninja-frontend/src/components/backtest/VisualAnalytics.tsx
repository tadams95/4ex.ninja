'use client';

import { useQuery } from '@tanstack/react-query';
import React, { useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  getVisualDatasets,
  simulateApiDelay,
  type VisualDatasets,
} from '../../lib/realOptimizationDataLoader';

/**
 * Visual Analytics Component
 *
 * Displays various analytical charts and heatmaps
 * Includes monthly performance heatmaps, drawdown analysis, etc.
 */
export default function VisualAnalytics() {
  const [selectedDataset, setSelectedDataset] = useState<string>('');

  const {
    data: visualData,
    isLoading,
    error,
  } = useQuery<VisualDatasets>({
    queryKey: ['backtest-visual-datasets'],
    queryFn: async () => {
      console.log('Loading visual datasets from local data');
      await simulateApiDelay();
      return getVisualDatasets();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-6 bg-neutral-700 rounded mb-4 w-48"></div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map(i => (
              <div
                key={i}
                className="h-64 bg-neutral-800 border border-neutral-700 rounded-lg"
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
        <p className="text-neutral-400 text-sm">Error loading visual data: {error.message}</p>
      </div>
    );
  }

  if (!visualData) {
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-neutral-300 mb-4">Visual Analytics</h3>
        <p className="text-neutral-400 text-sm">No visual data available</p>
      </div>
    );
  }

  // Convert the object to an array for easier handling
  const datasets = [
    {
      key: 'monthly_heatmap',
      title: 'Monthly Performance Heatmap',
      description: 'Seasonal performance patterns across different months',
      data: visualData.datasets.monthly_heatmap,
    },
    {
      key: 'drawdown_analysis',
      title: 'Drawdown Analysis',
      description: 'Risk assessment through drawdown periods',
      data: visualData.datasets.drawdown_analysis,
    },
    {
      key: 'win_rate_analysis',
      title: 'Win Rate Analysis',
      description: 'Success rate patterns across markets and timeframes',
      data: visualData.datasets.win_rate_analysis,
    },
    {
      key: 'risk_return_scatter',
      title: 'Risk vs Return Analysis',
      description: 'Strategy positioning - maximize return while minimizing risk',
      data: visualData.datasets.risk_return_scatter,
    },
    {
      key: 'comparison_matrix',
      title: 'Strategy Performance Matrix',
      description: 'Head-to-head comparison across key metrics',
      data: visualData.datasets.comparison_matrix,
    },
  ].filter(dataset => dataset.data);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-white">Visual Analytics</h2>
        <div className="text-sm text-neutral-400">{datasets.length} datasets available</div>
      </div>

      {/* Dataset Selection */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setSelectedDataset('')}
          className={`px-3 py-1 rounded-md text-sm transition-colors ${
            selectedDataset === ''
              ? 'bg-blue-600 text-white'
              : 'bg-neutral-700 text-neutral-300 hover:bg-neutral-600'
          }`}
        >
          All Datasets
        </button>
        {datasets.map(dataset => (
          <button
            key={dataset.key}
            onClick={() => setSelectedDataset(dataset.title)}
            className={`px-3 py-1 rounded-md text-sm transition-colors ${
              selectedDataset === dataset.title
                ? 'bg-blue-600 text-white'
                : 'bg-neutral-700 text-neutral-300 hover:bg-neutral-600'
            }`}
          >
            {dataset.title}
          </button>
        ))}
      </div>

      {/* Visual Datasets Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {datasets
          .filter(dataset => selectedDataset === '' || dataset.title === selectedDataset)
          .map(dataset => (
            <VisualDatasetCard key={dataset.key} dataset={dataset} />
          ))}
      </div>
    </div>
  );
}

interface DatasetCardProps {
  key: string;
  title: string;
  description: string;
  data: any;
}

/**
 * Individual Visual Dataset Card Component
 */
function VisualDatasetCard({ dataset }: { dataset: DatasetCardProps }) {
  const [showRawData, setShowRawData] = useState(false);

  const renderChart = () => {
    if (showRawData) {
      return (
        <div className="max-h-48 overflow-y-auto">
          <pre className="text-xs text-neutral-300 font-mono">
            {JSON.stringify(dataset.data, null, 2)}
          </pre>
        </div>
      );
    }

    // Render different chart types based on dataset key
    switch (dataset.key) {
      case 'risk_return_scatter':
        return <RiskReturnScatterChart data={dataset.data} />;

      case 'monthly_heatmap':
        return <MonthlyHeatmapChart data={dataset.data} />;

      case 'comparison_matrix':
        return <ComparisonMatrixChart data={dataset.data} />;

      case 'win_rate_analysis':
        return <WinRateAnalysisChart data={dataset.data} />;

      case 'drawdown_analysis':
        return <DrawdownAnalysisChart data={dataset.data} />;

      default:
        return <DataPreview data={dataset.data} />;
    }
  };

  return (
    <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white mb-2">{dataset.title}</h3>
          <p className="text-sm text-neutral-400">{dataset.description}</p>
        </div>
        <button
          onClick={() => setShowRawData(!showRawData)}
          className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
        >
          {showRawData ? 'Show Chart' : 'Show Data'}
        </button>
      </div>

      {/* Chart Area */}
      <div className="bg-neutral-900 border border-neutral-600 rounded-lg p-4 h-64">
        {renderChart()}
      </div>

      {/* Dataset Info */}
      <div className="mt-4 pt-4 border-t border-neutral-700">
        <div className="flex justify-between text-xs text-neutral-500">
          <span>
            Data Points:{' '}
            {Array.isArray(dataset.data) ? dataset.data.length : Object.keys(dataset.data).length}
          </span>
          <span>Interactive Chart</span>
        </div>
      </div>
    </div>
  );
}

/**
 * Risk vs Return Scatter Chart
 */
function RiskReturnScatterChart({ data }: { data: any }) {
  // Extract the data array from the structure
  const chartData = data?.data || [];

  if (!Array.isArray(chartData)) return <DataPreview data={data} />;

  // Define colors for different categories
  const categoryColors: Record<string, string> = {
    'Best Risk-Adjusted Returns': '#10b981', // green
    'Balanced Performance': '#3b82f6', // blue
    'High Return Balanced': '#f59e0b', // amber
    'Moderate Risk Strategies': '#8b5cf6', // purple
    'High Return High Risk': '#ef4444', // red
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ScatterChart margin={{ top: 20, right: 30, bottom: 40, left: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis
          type="number"
          dataKey="risk"
          domain={['dataMin - 1', 'dataMax + 1']}
          stroke="#9ca3af"
          fontSize={12}
          label={{
            value: 'Risk (Max Drawdown %)',
            position: 'insideBottom',
            offset: -5,
            style: { textAnchor: 'middle', fill: '#9ca3af' },
          }}
        />
        <YAxis
          type="number"
          dataKey="return"
          domain={['dataMin - 2', 'dataMax + 2']}
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
                  <p className="text-white font-semibold text-sm mb-1">{data.strategy}</p>
                  <p className="text-green-400 text-xs">Return: {data.return.toFixed(1)}%</p>
                  <p className="text-red-400 text-xs">Risk: {data.risk.toFixed(1)}%</p>
                  <p className="text-blue-400 text-xs">Sharpe: {data.sharpe.toFixed(2)}</p>
                  <p className="text-neutral-400 text-xs">{data.category}</p>
                </div>
              );
            }
            return null;
          }}
        />
        <Scatter data={chartData} fill="#8884d8">
          {chartData.map((entry: any, index: number) => (
            <Cell key={`cell-${index}`} fill={categoryColors[entry.category] || '#6b7280'} />
          ))}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  );
}

/**
 * Monthly Heatmap Chart (as Bar Chart)
 */
function MonthlyHeatmapChart({ data }: { data: any }) {
  if (!data?.data || typeof data.data !== 'object') return <DataPreview data={data} />;

  // Convert heatmap data to bar chart data
  const strategies = Object.keys(data.data);
  if (strategies.length === 0) return <DataPreview data={data} />;

  const firstStrategy = data.data[strategies[0]];
  if (!firstStrategy.months || !firstStrategy.returns) return <DataPreview data={data} />;

  const chartData = firstStrategy.months.map((month: string, index: number) => ({
    month,
    return: firstStrategy.returns[index],
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chartData} margin={{ top: 20, right: 30, bottom: 40, left: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis dataKey="month" stroke="#9ca3af" fontSize={12} />
        <YAxis
          stroke="#9ca3af"
          fontSize={12}
          label={{
            value: 'Monthly Return %',
            angle: -90,
            position: 'insideLeft',
            style: { textAnchor: 'middle', fill: '#9ca3af' },
          }}
        />
        <Tooltip
          content={({ active, payload, label }) => {
            if (active && payload && payload.length) {
              const value = payload[0].value as number;
              return (
                <div className="bg-neutral-800 border border-neutral-600 rounded-lg p-3 shadow-lg">
                  <p className="text-white font-semibold text-sm">{label}</p>
                  <p className={`text-sm ${value >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    Return: {value.toFixed(1)}%
                  </p>
                </div>
              );
            }
            return null;
          }}
        />
        <Bar dataKey="return">
          {chartData.map((entry: any, index: number) => (
            <Cell key={`cell-${index}`} fill={entry.return >= 0 ? '#10b981' : '#ef4444'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/**
 * Comparison Matrix Chart (as Radar Chart)
 */
function ComparisonMatrixChart({ data }: { data: any }) {
  if (!data || !data.strategies || !data.metrics) return <DataPreview data={data} />;

  // Convert matrix data to radar chart format
  const radarData = data.metrics.map((metric: string, index: number) => {
    const dataPoint: any = { metric };
    data.strategies.forEach((strategy: string) => {
      dataPoint[strategy] = data.data[strategy]?.[index] || 0;
    });
    return dataPoint;
  });

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

  return (
    <ResponsiveContainer width="100%" height="100%">
      <RadarChart data={radarData} margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
        <PolarGrid stroke="#374151" />
        <PolarAngleAxis dataKey="metric" className="text-xs fill-neutral-400" />
        <PolarRadiusAxis angle={0} domain={[0, 100]} tick={false} />
        {data.strategies.map((strategy: string, index: number) => (
          <Radar
            key={strategy}
            name={strategy.replace(/_/g, ' ')}
            dataKey={strategy}
            stroke={colors[index % colors.length]}
            fill={colors[index % colors.length]}
            fillOpacity={0.1}
            strokeWidth={2}
          />
        ))}
        <Legend wrapperStyle={{ fontSize: '10px' }} iconType="line" />
      </RadarChart>
    </ResponsiveContainer>
  );
}

/**
 * Win Rate Analysis Chart
 */
function WinRateAnalysisChart({ data }: { data: any }) {
  // Transform currency_pairs data into chart format
  const chartData = React.useMemo(() => {
    if (!data?.currency_pairs) {
      console.log('WinRateAnalysisChart: No currency_pairs data found', data);
      return [];
    }

    return Object.entries(data.currency_pairs).map(([pair, info]: [string, any]) => ({
      pair,
      win_rate: info.average_win_rate,
      strategy_count: info.strategy_count,
      consistency: info.consistency,
      win_rate_range: info.win_rate_range,
    }));
  }, [data]);

  if (chartData.length === 0) {
    return <DataPreview data={data} />;
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chartData} margin={{ top: 20, right: 30, bottom: 40, left: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis
          dataKey="pair"
          stroke="#9ca3af"
          fontSize={10}
          angle={-45}
          textAnchor="end"
          height={60}
        />
        <YAxis
          stroke="#9ca3af"
          fontSize={12}
          domain={[0, 100]}
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
              const data = payload[0].payload;
              return (
                <div className="bg-neutral-800 border border-neutral-600 rounded-lg p-3 shadow-lg">
                  <p className="text-white font-semibold text-sm mb-1">{label}</p>
                  <p className="text-green-400 text-xs">Win Rate: {data.win_rate}%</p>
                  <p className="text-blue-400 text-xs">Strategies: {data.strategy_count}</p>
                  <p className="text-purple-400 text-xs">Consistency: {data.consistency}%</p>
                  <p className="text-yellow-400 text-xs">
                    Range: {data.win_rate_range[0]}% - {data.win_rate_range[1]}%
                  </p>
                </div>
              );
            }
            return null;
          }}
        />
        <Bar dataKey="win_rate" fill="#3b82f6" />
      </BarChart>
    </ResponsiveContainer>
  );
}

/**
 * Drawdown Analysis Chart
 */
function DrawdownAnalysisChart({ data }: { data: any }) {
  // Transform strategy data into max drawdown summary
  const chartData = React.useMemo(() => {
    if (!data?.data) {
      console.log('DrawdownAnalysisChart: No data.data found', data);
      return [];
    }

    return Object.entries(data.data).map(([strategy, info]: [string, any]) => {
      const drawdowns = info.drawdowns || [];
      const maxDrawdown = Math.min(...drawdowns);
      const avgDrawdown =
        drawdowns.length > 0
          ? drawdowns.reduce((sum: number, dd: number) => sum + dd, 0) / drawdowns.length
          : 0;

      return {
        strategy: strategy.replace(/_/g, ' ').slice(0, 20) + '...',
        max_drawdown: Math.abs(maxDrawdown),
        avg_drawdown: Math.abs(avgDrawdown),
        full_name: strategy,
      };
    });
  }, [data]);

  if (chartData.length === 0) {
    return <DataPreview data={data} />;
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chartData} margin={{ top: 20, right: 30, bottom: 40, left: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis
          dataKey="strategy"
          stroke="#9ca3af"
          fontSize={10}
          angle={-45}
          textAnchor="end"
          height={60}
        />
        <YAxis
          stroke="#9ca3af"
          fontSize={12}
          label={{
            value: 'Max Drawdown %',
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
                  <p className="text-white font-semibold text-sm mb-1">{data.full_name}</p>
                  <p className="text-red-400 text-xs">
                    Max Drawdown: {data.max_drawdown.toFixed(2)}%
                  </p>
                  <p className="text-amber-400 text-xs">
                    Avg Drawdown: {data.avg_drawdown.toFixed(2)}%
                  </p>
                </div>
              );
            }
            return null;
          }}
        />
        <Bar dataKey="max_drawdown" fill="#ef4444" />
      </BarChart>
    </ResponsiveContainer>
  );
}

/**
 * Fallback Data Preview Component
 */
function DataPreview({ data }: { data: any }) {
  const sampleData = Array.isArray(data)
    ? data.slice(0, 5)
    : typeof data === 'object'
    ? Object.entries(data).slice(0, 5)
    : [];

  return (
    <div className="space-y-2 h-full overflow-y-auto">
      {Array.isArray(data) ? (
        <div className="space-y-1">
          {sampleData.map((item: any, idx: number) => (
            <div key={idx} className="text-xs text-neutral-400 font-mono">
              {typeof item === 'object' ? JSON.stringify(item).slice(0, 60) + '...' : item}
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-1">
          {sampleData.map(([key, value]: [string, any], idx: number) => (
            <div key={idx} className="text-xs text-neutral-400 font-mono">
              {key}:{' '}
              {typeof value === 'object' ? JSON.stringify(value).slice(0, 40) + '...' : value}
            </div>
          ))}
        </div>
      )}

      {(Array.isArray(data) ? data.length : Object.keys(data).length) > 5 && (
        <div className="text-xs text-neutral-500">
          ... and {(Array.isArray(data) ? data.length : Object.keys(data).length) - 5} more items
        </div>
      )}
    </div>
  );
}

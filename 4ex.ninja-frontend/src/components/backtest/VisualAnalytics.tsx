'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { mockVisualData, simulateApiDelay } from './mockData';

interface VisualDatasets {
  monthly_performance_heatmap: any;
  drawdown_analysis: any;
  win_rate_analysis: any;
  risk_return_scatter: any;
  comparison_matrix: any;
}

const API_BASE = 'http://157.230.58.248:8000';

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
      try {
        const response = await fetch(`${API_BASE}/api/v1/backtest/page/visual-datasets`);
        if (!response.ok) {
          throw new Error(`API not available: ${response.status}`);
        }
        const result = await response.json();
        return result.data; // Extract data from the response wrapper
      } catch (error) {
        // Fallback to mock data for development
        console.log('Using mock data for visual analytics (API not available)');
        await simulateApiDelay();
        return mockVisualData;
      }
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
      key: 'monthly_performance_heatmap',
      title: 'Monthly Performance Heatmap',
      description: 'Seasonal performance patterns across different months',
      data: visualData.monthly_performance_heatmap,
    },
    {
      key: 'drawdown_analysis',
      title: 'Drawdown Analysis',
      description: 'Risk assessment through drawdown periods',
      data: visualData.drawdown_analysis,
    },
    {
      key: 'win_rate_analysis',
      title: 'Win Rate Analysis',
      description: 'Success rate patterns across markets and timeframes',
      data: visualData.win_rate_analysis,
    },
    {
      key: 'risk_return_scatter',
      title: 'Risk vs Return Analysis',
      description: 'Strategy positioning - maximize return while minimizing risk',
      data: visualData.risk_return_scatter,
    },
    {
      key: 'comparison_matrix',
      title: 'Strategy Performance Matrix',
      description: 'Head-to-head comparison across key metrics',
      data: visualData.comparison_matrix,
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

  const renderChartPreview = () => {
    // For now, show data structure preview
    // In a full implementation, this would render actual charts based on chart_type
    const sampleData = Array.isArray(dataset.data)
      ? dataset.data.slice(0, 5)
      : typeof dataset.data === 'object'
      ? Object.entries(dataset.data).slice(0, 5)
      : [];

    return (
      <div className="space-y-2">
        {Array.isArray(dataset.data) ? (
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

        {(Array.isArray(dataset.data) ? dataset.data.length : Object.keys(dataset.data).length) >
          5 && (
          <div className="text-xs text-neutral-500">
            ... and{' '}
            {(Array.isArray(dataset.data)
              ? dataset.data.length
              : Object.keys(dataset.data).length) - 5}{' '}
            more items
          </div>
        )}
      </div>
    );
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
          {showRawData ? 'Hide' : 'Show'} Data
        </button>
      </div>

      {/* Chart Preview Area */}
      <div className="bg-neutral-900 border border-neutral-600 rounded-lg p-4 min-h-32">
        {showRawData ? (
          <div className="max-h-48 overflow-y-auto">
            <pre className="text-xs text-neutral-300 font-mono">
              {JSON.stringify(dataset.data, null, 2)}
            </pre>
          </div>
        ) : (
          renderChartPreview()
        )}
      </div>

      {/* Dataset Info */}
      <div className="mt-4 pt-4 border-t border-neutral-700">
        <div className="flex justify-between text-xs text-neutral-500">
          <span>
            Data Points:{' '}
            {Array.isArray(dataset.data) ? dataset.data.length : Object.keys(dataset.data).length}
          </span>
          <span>Analytics Dataset</span>
        </div>
      </div>
    </div>
  );
}

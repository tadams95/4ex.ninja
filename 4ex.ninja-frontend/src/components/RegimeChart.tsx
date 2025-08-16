'use client';

import {
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
} from 'chart.js';
import { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

interface RegimeChartProps {
  timeframe?: string;
  className?: string;
}

interface ChartDataset {
  label: string;
  data: number[];
  borderColor: string;
  backgroundColor: string;
  tension?: number;
  yAxisID?: string;
}

interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

export function RegimeChart({ timeframe = '24h', className = '' }: RegimeChartProps) {
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchChartData = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(
          `${process.env.NEXT_PUBLIC_MONITORING_API_URL}/charts/regime-timeline?timeframe=${timeframe}`
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setChartData(data);
      } catch (error) {
        console.error('Failed to fetch chart data:', error);
        setError('Failed to load chart data');
      } finally {
        setLoading(false);
      }
    };

    fetchChartData();

    // Update chart data every minute
    const interval = setInterval(fetchChartData, 60000);

    return () => clearInterval(interval);
  }, [timeframe]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: '#D4D4D8',
          font: {
            size: 12,
          },
        },
      },
      title: {
        display: true,
        text: `Market Regime Analysis - ${timeframe.toUpperCase()}`,
        color: '#D4D4D8',
        font: {
          size: 14,
          weight: 'bold' as const,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#FFFFFF',
        bodyColor: '#D4D4D8',
        borderColor: '#374151',
        borderWidth: 1,
      },
    },
    scales: {
      x: {
        ticks: {
          color: '#A1A1AA',
          font: {
            size: 10,
          },
        },
        grid: {
          color: 'rgba(161, 161, 170, 0.1)',
        },
      },
      y: {
        position: 'left' as const,
        ticks: {
          color: '#A1A1AA',
          font: {
            size: 10,
          },
          callback: function (value: any) {
            const regimeMap: { [key: number]: string } = {
              4: 'Trending High Vol',
              3: 'Trending Low Vol',
              2: 'Ranging High Vol',
              1: 'Ranging Low Vol',
            };
            return regimeMap[value as number] || value;
          },
        },
        grid: {
          color: 'rgba(161, 161, 170, 0.1)',
        },
        min: 0,
        max: 5,
      },
      confidence: {
        type: 'linear' as const,
        position: 'right' as const,
        ticks: {
          color: '#A1A1AA',
          font: {
            size: 10,
          },
        },
        grid: {
          display: false,
        },
        min: 0,
        max: 100,
      },
    },
    interaction: {
      intersect: false,
      mode: 'index' as const,
    },
  };

  if (loading) {
    return (
      <div
        className={`h-64 bg-neutral-800 rounded-lg animate-pulse flex items-center justify-center ${className}`}
      >
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-neutral-400">Loading chart...</span>
        </div>
      </div>
    );
  }

  if (error || !chartData) {
    return (
      <div
        className={`h-64 bg-neutral-800 rounded-lg flex items-center justify-center ${className}`}
      >
        <div className="text-center">
          <div className="text-red-400 mb-2">⚠️</div>
          <span className="text-neutral-400 text-sm">{error || 'No chart data available'}</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`h-64 w-full ${className}`}>
      <Line data={chartData} options={options} />
    </div>
  );
}

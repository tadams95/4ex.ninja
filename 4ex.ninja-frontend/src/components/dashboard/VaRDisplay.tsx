import { useEffect, useState } from 'react';

interface VaRData {
  portfolio_var: {
    parametric: number;
    historical: number;
    monte_carlo: number;
    confidence_level: number;
  };
  risk_metrics: {
    total_exposure: number;
    risk_utilization: number;
    var_limit: number;
    breaches_today: number;
  };
  timestamp: string;
  status: string;
}

interface VaRDisplayProps {
  refreshInterval?: number; // in seconds, default 30
}

export default function VaRDisplay({ refreshInterval = 30 }: VaRDisplayProps) {
  const [varData, setVarData] = useState<VaRData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const TARGET_VAR_PERCENT = 0.31; // 0.31% target

  const fetchVaRData = async () => {
    try {
      const response = await fetch('/api/risk/var-summary');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setVarData(data);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch VaR data');
      console.error('VaR fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchVaRData();

    // Set up auto-refresh
    const interval = setInterval(fetchVaRData, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const getVaRStatus = (currentVaR: number, target: number) => {
    const percentVaR = (currentVaR / (varData?.risk_metrics.total_exposure || 1)) * 100;
    if (percentVaR <= target) {
      return {
        status: 'Within Target',
        color: 'text-green-600 dark:text-green-400',
        bgColor: 'bg-green-100 dark:bg-green-900',
      };
    } else if (percentVaR <= target * 1.2) {
      return {
        status: 'Warning',
        color: 'text-yellow-600 dark:text-yellow-400',
        bgColor: 'bg-yellow-100 dark:bg-yellow-900',
      };
    } else {
      return {
        status: 'Breach Alert',
        color: 'text-red-600 dark:text-red-400',
        bgColor: 'bg-red-100 dark:bg-red-900',
      };
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600 dark:text-gray-300">
            Current VaR (95% confidence)
          </span>
          <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">Loading...</span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div className="bg-blue-600 h-2 rounded-full w-1/2 animate-pulse"></div>
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400">
          Target: {TARGET_VAR_PERCENT}% | Status: Loading...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
          <div className="flex items-center">
            <div className="text-red-500 dark:text-red-400 mr-2">⚠️</div>
            <div>
              <div className="font-medium text-red-800 dark:text-red-200">
                Failed to load VaR data
              </div>
              <div className="text-sm text-red-600 dark:text-red-300 mt-1">{error}</div>
            </div>
          </div>
        </div>
        <button
          onClick={() => {
            setLoading(true);
            setError(null);
            fetchVaRData();
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!varData) {
    return <div>No VaR data available</div>;
  }

  const currentVaR = varData.portfolio_var.historical; // Using historical VaR as primary
  const totalExposure = varData.risk_metrics.total_exposure;
  const varPercentage = (currentVaR / totalExposure) * 100;
  const targetPercentage = TARGET_VAR_PERCENT;
  const progressPercentage = Math.min((varPercentage / targetPercentage) * 100, 100);
  const statusInfo = getVaRStatus(currentVaR, targetPercentage);

  return (
    <div className="space-y-4">
      {/* Main VaR Display */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-600 dark:text-gray-300">
          Current VaR (95% confidence)
        </span>
        <div className="text-right">
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {formatCurrency(currentVaR)}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {formatPercentage(varPercentage / 100)} of portfolio
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all duration-500 ${
              progressPercentage <= 80
                ? 'bg-green-500'
                : progressPercentage <= 100
                ? 'bg-yellow-500'
                : 'bg-red-500'
            }`}
            style={{ width: `${Math.min(progressPercentage, 100)}%` }}
          ></div>
        </div>
        <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>0%</span>
          <span>Target: {targetPercentage}%</span>
          <span>{formatPercentage(varPercentage / 100)}</span>
        </div>
      </div>

      {/* Status and Details */}
      <div className="space-y-3">
        <div
          className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusInfo.bgColor} ${statusInfo.color}`}
        >
          {statusInfo.status}
        </div>

        {/* VaR Methods Comparison */}
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
            <div className="font-medium text-gray-900 dark:text-white">Historical</div>
            <div className="text-blue-600 dark:text-blue-400">
              {formatCurrency(varData.portfolio_var.historical)}
            </div>
          </div>
          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
            <div className="font-medium text-gray-900 dark:text-white">Parametric</div>
            <div className="text-green-600 dark:text-green-400">
              {formatCurrency(varData.portfolio_var.parametric)}
            </div>
          </div>
          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
            <div className="font-medium text-gray-900 dark:text-white">Monte Carlo</div>
            <div className="text-purple-600 dark:text-purple-400">
              {formatCurrency(varData.portfolio_var.monte_carlo)}
            </div>
          </div>
        </div>

        {/* Risk Metrics */}
        <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400">
          <span>Total Exposure: {formatCurrency(totalExposure)}</span>
          <span>Breaches Today: {varData.risk_metrics.breaches_today}</span>
        </div>

        {/* Last Updated */}
        {lastUpdated && (
          <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
}

import { useRiskData } from '@/hooks/useRiskData';

interface VaRDisplayProps {
  refreshInterval?: number; // in milliseconds, default 30000 (30 seconds)
}

export default function VaRDisplay({ refreshInterval = 30000 }: VaRDisplayProps) {
  const { varData, loading, error, lastUpdate, refetch } = useRiskData(refreshInterval);

  const TARGET_VAR_PERCENT = 0.31; // 0.31% target

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const calculateRiskLevel = (currentVaR: number, targetVaR: number): string => {
    const percentVaR = (currentVaR / (varData?.risk_metrics.total_exposure || 1)) * 100;

    if (percentVaR > targetVaR * 1.5) return 'HIGH';
    if (percentVaR > targetVaR * 1.2) return 'MEDIUM';
    return 'LOW';
  };

  const getProgressColor = (level: string): string => {
    switch (level) {
      case 'HIGH':
        return 'bg-red-500';
      case 'MEDIUM':
        return 'bg-yellow-500';
      default:
        return 'bg-green-500';
    }
  };

  const getProgressPercentage = (currentVaR: number): number => {
    if (!varData?.risk_metrics.total_exposure) return 0;

    const percentVaR = (currentVaR / varData.risk_metrics.total_exposure) * 100;
    const targetPercentage = TARGET_VAR_PERCENT;

    // Show as percentage of target (100% = at target)
    return Math.min((percentVaR / targetPercentage) * 100, 100);
  };

  if (loading) {
    return (
      <div className="p-6 bg-neutral-800 rounded-lg border border-neutral-700 shadow-lg">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-white mb-1">VaR Monitor</h3>
          <p className="text-sm text-neutral-400">Loading risk data...</p>
        </div>

        <div className="space-y-4">
          <div className="animate-pulse">
            <div className="h-4 bg-neutral-600 rounded w-3/4 mb-2"></div>
            <div className="h-6 bg-neutral-600 rounded w-1/2 mb-4"></div>
            <div className="grid grid-cols-3 gap-4">
              <div className="h-16 bg-neutral-600 rounded"></div>
              <div className="h-16 bg-neutral-600 rounded"></div>
              <div className="h-16 bg-neutral-600 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-neutral-800 rounded-lg border border-red-500/30 shadow-lg">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-red-400 mb-1">VaR Monitor - Error</h3>
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

  if (!varData) {
    return (
      <div className="p-6 bg-neutral-800 rounded-lg border border-neutral-700 shadow-lg">
        <h3 className="text-lg font-semibold text-white mb-1">VaR Monitor</h3>
        <p className="text-sm text-neutral-400">No VaR data available</p>
      </div>
    );
  }

  const currentVaR = varData.portfolio_var.historical; // Using historical VaR as primary
  const totalExposure = varData.risk_metrics.total_exposure;
  const riskLevel = calculateRiskLevel(currentVaR, TARGET_VAR_PERCENT);
  const targetPercentage = TARGET_VAR_PERCENT;
  const progressPercentage = getProgressPercentage(currentVaR);
  const progressColor = getProgressColor(riskLevel);

  return (
    <div className="p-6 bg-neutral-800 rounded-lg border border-neutral-700 shadow-lg">
      {/* Header */}
      <div className="mb-4">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-semibold text-white mb-1">VaR Monitor</h3>
            <p className="text-sm text-neutral-400">
              Last updated: {formatTime(lastUpdate)} | Risk Level:{' '}
              <span
                className={`font-semibold ${
                  riskLevel === 'HIGH'
                    ? 'text-red-400'
                    : riskLevel === 'MEDIUM'
                    ? 'text-yellow-400'
                    : 'text-green-400'
                }`}
              >
                {riskLevel}
              </span>
            </p>
          </div>
          <button
            onClick={refetch}
            className="px-3 py-1 text-sm bg-neutral-700 text-neutral-300 rounded hover:bg-neutral-600 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Primary VaR Display */}
      <div className="mb-6">
        <div className="flex justify-between items-end mb-2">
          <span className="text-sm font-medium text-neutral-300">Historical VaR (95%)</span>
          <span className="text-sm text-neutral-400">
            Target: {(targetPercentage * 100).toFixed(2)}%
          </span>
        </div>

        <div className="flex items-baseline space-x-3 mb-3">
          <span className="text-3xl font-bold text-white">{formatCurrency(currentVaR)}</span>
          <span className="text-lg text-neutral-300">
            ({((currentVaR / totalExposure) * 100).toFixed(2)}%)
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-neutral-600 rounded-full h-3 mb-2">
          <div
            className={`h-3 rounded-full transition-all duration-300 ${progressColor}`}
            style={{ width: `${progressPercentage}%` }}
          ></div>
        </div>
        <div className="flex justify-between text-xs text-neutral-400">
          <span>0%</span>
          <span>{targetPercentage * 100}% Target</span>
        </div>
      </div>

      {/* VaR Methods Comparison */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center p-3 bg-blue-900/30 rounded-lg border border-blue-500/30">
          <div className="text-sm font-medium text-blue-400 mb-1">Parametric</div>
          <div className="text-lg font-semibold text-blue-300">
            {formatCurrency(varData.portfolio_var.parametric)}
          </div>
        </div>

        <div className="text-center p-3 bg-green-900/30 rounded-lg border border-green-500/30">
          <div className="text-sm font-medium text-green-400 mb-1">Historical</div>
          <div className="text-lg font-semibold text-green-300">
            {formatCurrency(varData.portfolio_var.historical)}
          </div>
        </div>

        <div className="text-center p-3 bg-purple-900/30 rounded-lg border border-purple-500/30">
          <div className="text-sm font-medium text-purple-400 mb-1">Monte Carlo</div>
          <div className="text-lg font-semibold text-purple-300">
            {formatCurrency(varData.portfolio_var.monte_carlo)}
          </div>
        </div>
      </div>

      {/* Risk Metrics Summary */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="space-y-1">
          <div className="flex justify-between">
            <span className="text-neutral-400">Total Exposure:</span>
            <span className="font-medium text-white">{formatCurrency(totalExposure)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-neutral-400">VaR Utilization:</span>
            <span className="font-medium text-white">
              {((varData.risk_metrics.risk_utilization || 0) * 100).toFixed(1)}%
            </span>
          </div>
        </div>

        <div className="space-y-1">
          <div className="flex justify-between">
            <span className="text-neutral-400">VaR Limit:</span>
            <span className="font-medium text-white">
              {formatCurrency(varData.risk_metrics.var_limit || 0)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-neutral-400">Breaches Today:</span>
            <span
              className={`font-medium ${
                (varData.risk_metrics.breaches_today || 0) > 0 ? 'text-red-400' : 'text-green-400'
              }`}
            >
              {varData.risk_metrics.breaches_today || 0}
            </span>
          </div>
        </div>
      </div>

      {/* Status Footer */}
      <div className="mt-4 pt-3 border-t border-neutral-600">
        <div className="flex justify-between items-center text-xs text-neutral-400">
          <span>Confidence Level: {varData.portfolio_var.confidence_level}%</span>
          <span
            className={`px-2 py-1 rounded-full text-xs font-medium ${
              varData.status === 'active'
                ? 'bg-green-900/30 text-green-400 border border-green-500/30'
                : 'bg-neutral-700 text-neutral-300 border border-neutral-600'
            }`}
          >
            {varData.status}
          </span>
        </div>
      </div>
    </div>
  );
}

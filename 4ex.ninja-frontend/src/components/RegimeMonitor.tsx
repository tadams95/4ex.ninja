/**
 * RegimeMonitor Component
 * Displays current market regime status and confidence metrics
 */

'use client';

import React from 'react';
import { type RegimeStatus } from '../hooks/useRegimeData';
import { Card } from './ui/Card';

interface RegimeMonitorProps {
  regimeStatus: RegimeStatus | null;
  loading: boolean;
  lastUpdate: Date;
}

const getRegimeColor = (regime: string): string => {
  const colorMap: Record<string, string> = {
    trending_high_vol: 'text-red-400',
    trending_low_vol: 'text-green-400',
    ranging_high_vol: 'text-orange-400',
    ranging_low_vol: 'text-blue-400',
    crisis: 'text-red-600',
    recovery: 'text-emerald-400',
  };
  return colorMap[regime] || 'text-gray-400';
};

const getRegimeDescription = (regime: string): string => {
  const descriptions: Record<string, string> = {
    trending_high_vol: 'Strong trending market with high volatility',
    trending_low_vol: 'Trending market with low volatility',
    ranging_high_vol: 'Sideways market with high volatility',
    ranging_low_vol: 'Consolidating market with low volatility',
    crisis: 'Crisis conditions - extreme volatility',
    recovery: 'Market recovery phase',
  };
  return descriptions[regime] || 'Unknown market regime';
};

const formatTimeInRegime = (hours: number): string => {
  if (hours < 1) return `${Math.round(hours * 60)}m`;
  if (hours < 24) return `${Math.round(hours)}h`;
  return `${Math.round(hours / 24)}d`;
};

export const RegimeMonitor: React.FC<RegimeMonitorProps> = ({
  regimeStatus,
  loading,
  lastUpdate,
}) => {
  if (loading) {
    return (
      <Card className="animate-pulse">
        <div className="h-6 bg-neutral-600 rounded mb-4"></div>
        <div className="h-4 bg-neutral-600 rounded mb-2"></div>
        <div className="h-4 bg-neutral-600 rounded w-2/3"></div>
      </Card>
    );
  }

  if (!regimeStatus) {
    return (
      <Card>
        <h3 className="text-lg font-semibold text-red-400 mb-2">Regime Monitor Unavailable</h3>
        <p className="text-neutral-400">Unable to fetch regime data. Check API connection.</p>
      </Card>
    );
  }

  const confidencePercentage = Math.round(regimeStatus.confidence * 100);
  const strengthPercentage = Math.round(regimeStatus.regime_strength * 100);

  return (
    <Card className="border border-neutral-600">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Market Regime</h3>
        <span className="text-xs text-neutral-400">Updated: {lastUpdate.toLocaleTimeString()}</span>
      </div>

      {/* Current Regime Display */}
      <div className="mb-6">
        <div className={`text-2xl font-bold mb-2 ${getRegimeColor(regimeStatus.current_regime)}`}>
          {regimeStatus.current_regime.replace(/_/g, ' ').toUpperCase()}
        </div>
        <p className="text-neutral-300 text-sm">
          {getRegimeDescription(regimeStatus.current_regime)}
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-neutral-700 rounded-lg p-3">
          <div className="text-xs text-neutral-400 mb-1">Confidence</div>
          <div className="flex items-center">
            <div className="text-lg font-semibold text-white">{confidencePercentage}%</div>
            <div className="ml-2 flex-1 bg-neutral-600 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${
                  confidencePercentage >= 70
                    ? 'bg-green-500'
                    : confidencePercentage >= 50
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }`}
                style={{ width: `${confidencePercentage}%` }}
              ></div>
            </div>
          </div>
        </div>

        <div className="bg-neutral-700 rounded-lg p-3">
          <div className="text-xs text-neutral-400 mb-1">Regime Strength</div>
          <div className="flex items-center">
            <div className="text-lg font-semibold text-white">{strengthPercentage}%</div>
            <div className="ml-2 flex-1 bg-neutral-600 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-blue-500 transition-all duration-300"
                style={{ width: `${strengthPercentage}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Additional Info */}
      <div className="grid grid-cols-3 gap-3 text-sm">
        <div className="text-center">
          <div className="text-neutral-400">Time in Regime</div>
          <div className="text-white font-medium">
            {formatTimeInRegime(regimeStatus.time_in_regime)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-neutral-400">Volatility</div>
          <div
            className={`font-medium ${
              regimeStatus.volatility_level === 'high' ? 'text-red-400' : 'text-green-400'
            }`}
          >
            {regimeStatus.volatility_level}
          </div>
        </div>
        <div className="text-center">
          <div className="text-neutral-400">Trend</div>
          <div
            className={`font-medium ${
              regimeStatus.trend_direction === 'up'
                ? 'text-green-400'
                : regimeStatus.trend_direction === 'down'
                ? 'text-red-400'
                : 'text-yellow-400'
            }`}
          >
            {regimeStatus.trend_direction}
          </div>
        </div>
      </div>
    </Card>
  );
};

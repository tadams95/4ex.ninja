'use client';

import { FeedErrorBoundary } from '@/components/error';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';
import {
  usePageNavigationTracking,
  useRenderPerformance,
  useSignalLoadTracking,
} from '@/hooks/usePerformance';
import { Crossover } from '@/types';
import Link from 'next/link';
import React, { useCallback, useEffect, useMemo, useState } from 'react';

// Define signal type to match the new database structure
interface Signal {
  _id: string;
  id: string;
  pair: string;
  type: 'BUY' | 'SELL'; // signal_type from database
  timeframe: string;
  entry: string; // price from database
  confidence: string;
  strategy_type: string;
  timestamp: string | Date;
  created_at: string | Date;
  status: string;
  fast_ma: string;
  slow_ma: string;
  // Map signal properties to crossover-like properties for compatibility
  crossoverType?: 'BULLISH' | 'BEARISH';
}

function InsightsPage() {
  // Get auth context for user info
  const { user, isAuthenticated } = useAuth();

  // Performance monitoring hooks
  useRenderPerformance('InsightsPage');
  usePageNavigationTracking('insights');
  const trackSignalLoad = useSignalLoadTracking();

  // State management for signals (similar to sigcheck page)
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEmpty, setIsEmpty] = useState(false);

  // Fetch signals function (similar to sigcheck page)
  const fetchSignals = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      setIsEmpty(false);

      const response = await fetch('/api/signals');

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch signals');
      }

      const data = await response.json();
      setSignals(data.signals || []);

      // Check if API returned isEmpty flag
      if (data.isEmpty) {
        setIsEmpty(true);
      }
    } catch (err: any) {
      console.error('Error fetching signals:', err);
      setError(err?.message || 'Failed to load signals. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Set up fetching and polling (similar to sigcheck page)
  useEffect(() => {
    fetchSignals();

    // Optional: Set up polling to refresh signals periodically
    const intervalId = setInterval(fetchSignals, 5 * 60 * 1000); // Every 5 minutes

    return () => clearInterval(intervalId);
  }, [fetchSignals]);

  // Create crossoverData structure to maintain compatibility with existing UI
  const crossoverData = useMemo(
    () => ({
      crossovers: signals,
      isEmpty: isEmpty || signals.length === 0,
    }),
    [signals, isEmpty]
  );

  // Track signal loading performance
  useEffect(() => {
    if (!loading && crossoverData) {
      const endTracking = trackSignalLoad(crossoverData.crossovers?.length || 0);
      endTracking();
    }
  }, [loading, crossoverData, trackSignalLoad]);

  // Memoize expensive data processing
  const processedData = useMemo(() => {
    const crossovers = crossoverData?.crossovers || [];
    const isEmpty = crossoverData?.isEmpty || crossovers.length === 0;

    // Map signals to crossover-like format for compatibility and sort by timestamp
    const mappedCrossovers: Crossover[] = crossovers.map((signal: Signal) => ({
      _id: signal._id,
      pair: signal.pair,
      crossoverType: signal.type === 'BUY' ? 'BULLISH' : ('BEARISH' as 'BULLISH' | 'BEARISH'),
      timeframe: signal.timeframe,
      fastMA: parseFloat(signal.fast_ma) || 20, // Use actual fast_ma from signal
      slowMA: parseFloat(signal.slow_ma) || 50, // Use actual slow_ma from signal
      price: signal.entry,
      timestamp:
        typeof signal.timestamp === 'string' ? new Date(signal.timestamp) : signal.timestamp,
      signal: signal.type === 'BUY' ? 'Buy' : ('Sell' as 'Buy' | 'Sell'),
      close: parseFloat(signal.entry) || 0,
      confidence: parseFloat(signal.confidence) || 0,
      strategy_type: signal.strategy_type,
      status: signal.status,
    }));

    const sortedCrossovers = [...mappedCrossovers].sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );

    const bullishCount = mappedCrossovers.filter(c => c.crossoverType === 'BULLISH').length;
    const bearishCount = mappedCrossovers.filter(c => c.crossoverType === 'BEARISH').length;
    const totalSignals = mappedCrossovers.length;
    const bullishPercentage =
      totalSignals > 0 ? ((bullishCount / totalSignals) * 100).toFixed(1) : '0';

    return {
      crossovers: sortedCrossovers,
      isEmpty,
      stats: {
        bullishCount,
        bearishCount,
        totalSignals,
        bullishPercentage,
      },
    };
  }, [crossoverData]);

  const handleRetry = useCallback((): void => {
    fetchSignals();
  }, [fetchSignals]);

  const handleCrossoverClick = useCallback((crossover: Crossover) => {
    // Handle crossover item clicks (e.g., show details, navigate to analysis)
    console.log('Crossover clicked:', crossover);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white">
        {/* Loading Header */}
        <div className="border-b border-neutral-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between py-6">
              <div>
                <div className="flex items-center space-x-3 mb-2">
                  <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse"></div>
                  <div className="h-8 bg-neutral-700 rounded w-80 animate-pulse"></div>
                </div>
                <div className="h-4 bg-neutral-800 rounded w-64 animate-pulse"></div>
              </div>
              <div className="flex space-x-4">
                {[1, 2, 3].map(i => (
                  <div
                    key={i}
                    className="px-4 py-3 bg-neutral-700 rounded-lg animate-pulse w-24 h-16"
                  ></div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Loading Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="space-y-8">
            <div className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-xl h-32"></div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[1, 2, 3].map(i => (
                <div
                  key={i}
                  className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-lg h-24"
                />
              ))}
            </div>
            <div className="animate-pulse bg-neutral-800 border border-neutral-700 rounded-lg h-96"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black text-white">
        {/* Error Header */}
        <div className="border-b border-neutral-700 ">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between py-6">
              <div>
                <div className="flex items-center space-x-3 mb-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                  <h1 className="text-3xl font-bold text-white">Market Intelligence Feed</h1>
                </div>
                <p className="text-neutral-400 text-sm">Error loading real-time market insights</p>
              </div>
            </div>
          </div>
        </div>

        {/* Error Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <div className="bg-red-900/20 border border-red-700 rounded-xl p-8 max-w-md mx-auto">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-16 w-16 mx-auto mb-4 text-red-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <h3 className="text-xl font-bold text-red-400 mb-4">
                Unable to Load Market Insights
              </h3>
              <p className="text-neutral-400 mb-6">
                {error || 'An unexpected error occurred while loading market data'}
              </p>
              <button
                onClick={handleRetry}
                className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
              >
                Retry Loading
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Enhanced Header */}
      <div className="border-b border-neutral-700 ">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <div>
              <div className="flex items-center space-x-3 mb-2">
                <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
                <h1 className="text-3xl font-bold text-white">Market Intelligence Feed</h1>
              </div>
              <p className="text-neutral-400 text-sm mb-1">
                Real-time insights from Enhanced Daily EMA Strategy
              </p>
              <p className="text-neutral-500 text-xs">
                Connected:{' '}
                {user?.walletAddress
                  ? `${user.walletAddress.slice(0, 6)}...${user.walletAddress.slice(-4)}`
                  : 'Wallet'}{' '}
                • Live Feed Active
              </p>
            </div>

            {/* Live Stats Summary */}
            <div className="flex items-center space-x-6">
              {/* <div className="flex space-x-4">
                <div className="text-center px-4 py-3 bg-green-900/30 border border-green-700 rounded-lg">
                  <div className="text-2xl font-bold text-green-400">
                    {processedData.stats.bullishCount}
                  </div>
                  <div className="text-xs text-green-300">Bull Signals</div>
                </div>
                <div className="text-center px-4 py-3 bg-red-900/30 border border-red-700 rounded-lg">
                  <div className="text-2xl font-bold text-red-400">
                    {processedData.stats.bearishCount}
                  </div>
                  <div className="text-xs text-red-300">Bear Signals</div>
                </div>
                <div className="text-center px-4 py-3 bg-blue-900/30 border border-blue-700 rounded-lg">
                  <div className="text-lg font-bold text-blue-400">
                    {processedData.stats.bullishPercentage}%
                  </div>
                  <div className="text-xs text-blue-300">Bull Rate</div>
                </div>
              </div> */}

              <div className="flex items-center space-x-4">
                <Link
                  href="/account"
                  className="px-4 py-2 text-sm bg-neutral-800 text-neutral-300 rounded-lg hover:bg-neutral-700 transition-colors border border-neutral-600"
                >
                  Account
                </Link>
                <div className="flex items-center space-x-2 text-sm text-neutral-400">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span>Live</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Signals Grid */}
        {processedData.isEmpty || processedData.crossovers.length === 0 ? (
          <div className="bg-neutral-800 border border-neutral-700 rounded-xl p-12 text-center">
            <div className="max-w-md mx-auto">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-20 w-20 mx-auto mb-6 text-neutral-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <h3 className="text-2xl font-bold text-white mb-4">No Active Signals</h3>
              <p className="text-neutral-400 mb-2">
                Our Enhanced Daily EMA Strategy is continuously monitoring market conditions.
              </p>
              <p className="text-neutral-500 text-sm">
                New opportunities will appear here as soon as our technical analysis system detects
                favorable conditions across major currency pairs.
              </p>
              <div className="mt-6 flex items-center justify-center space-x-2 text-sm text-neutral-400">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                <span>System actively scanning markets</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Signals Header */}
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-white">Active Market Signals</h2>
                <p className="text-neutral-400 text-sm">
                  {processedData.crossovers.length} signal
                  {processedData.crossovers.length !== 1 ? 's' : ''} detected
                </p>
              </div>
              <div className="text-right text-sm text-neutral-400">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>{processedData.stats.bullishCount} Bullish</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    <span>{processedData.stats.bearishCount} Bearish</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Signals Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {processedData.crossovers.map((crossover, index) => (
                <SignalCard
                  key={crossover._id}
                  crossover={crossover}
                  index={index}
                  onClick={handleCrossoverClick}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Individual Signal Card Component
 */
interface SignalCardProps {
  crossover: Crossover;
  index: number;
  onClick?: (crossover: Crossover) => void;
}

function SignalCard({ crossover, index, onClick }: SignalCardProps) {
  const handleClick = () => {
    if (onClick) {
      onClick(crossover);
    }
  };

  const borderColor = crossover.crossoverType === 'BULLISH' ? 'border-green-500' : 'border-red-500';
  const badgeStyle =
    crossover.crossoverType === 'BULLISH'
      ? 'bg-green-500/20 text-green-500 border-green-500/30'
      : 'bg-red-500/20 text-red-400 border-red-500/30';

  return (
    <div
      className={`bg-neutral-800 rounded-lg p-5 shadow-lg border-l-4 ${borderColor} cursor-pointer hover:bg-neutral-700 transition-all duration-200 hover:scale-[1.02] border border-neutral-600`}
      onClick={handleClick}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-bold text-white">{crossover.pair}</h3>
        <span className={`px-2 py-1 rounded-md text-xs font-medium border ${badgeStyle}`}>
          {crossover.crossoverType}
        </span>
      </div>

      {/* Signal Details */}
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-neutral-400">Timeframe:</span>
          <span className="font-medium text-white">{crossover.timeframe}</span>
        </div>

        <div className="flex justify-between">
          <span className="text-neutral-400">Price:</span>
          <span className="font-medium text-white">{crossover.price}</span>
        </div>

        {crossover.confidence && (
          <div className="flex justify-between">
            <span className="text-neutral-400">Confidence:</span>
            <span className="font-medium text-blue-400">
              {(crossover.confidence * 100).toFixed(0)}%
            </span>
          </div>
        )}

        {crossover.strategy_type && (
          <div className="flex justify-between">
            <span className="text-neutral-400">Strategy:</span>
            <span className="font-medium text-purple-400">{crossover.strategy_type}</span>
          </div>
        )}

        {crossover.status && (
          <div className="flex justify-between">
            <span className="text-neutral-400">Status:</span>
            <span
              className={`font-medium ${
                crossover.status === 'ACTIVE' ? 'text-green-400' : 'text-neutral-500'
              }`}
            >
              {crossover.status}
            </span>
          </div>
        )}
      </div>

      {/* Timestamp */}
      <div className="mt-4 pt-3 border-t border-neutral-700">
        <p className="text-xs text-neutral-500">{new Date(crossover.timestamp).toLocaleString()}</p>
      </div>
    </div>
  );
}

// Wrap the component with ProtectedRoute and FeedErrorBoundary
export default function ProtectedInsightsPage(): React.ReactElement {
  return (
    <ProtectedRoute requireWallet={true}>
      <FeedErrorBoundary>
        <InsightsPage />
      </FeedErrorBoundary>
    </ProtectedRoute>
  );
}

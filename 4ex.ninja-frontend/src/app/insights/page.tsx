'use client';

import { FeedErrorBoundary } from '@/components/error';
import ProtectedRoute from '@/components/ProtectedRoute';
import { LoadingSequence } from '@/components/ui';
import VirtualizedCrossoverList from '@/components/VirtualizedCrossoverList';
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
    return <LoadingSequence type="trading" />;
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 md:px-6 lg:px-8 py-8 max-w-2xl bg-black min-h-screen">
        <h1 className="text-3xl font-bold mb-6">Market Intelligence Feed</h1>
        <div className="bg-red-500/20 text-red-400 p-6 rounded-md flex flex-col items-center">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-12 w-12 mb-2"
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
          <p className="font-medium mb-2">Error loading market insights</p>
          <p className="text-sm">{error || 'An error occurred'}</p>
          <button
            onClick={handleRetry}
            className="mt-4 px-4 py-2 bg-red-500/30 text-red-300 rounded-md hover:bg-red-500/40 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 md:px-6 lg:px-8 py-8 max-w-2xl bg-black min-h-screen">
      {/* Welcome Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white">Market Movement Insights</h1>
          <p className="text-gray-400 text-sm mt-1">
            Connected:{' '}
            {user?.walletAddress
              ? `${user.walletAddress.slice(0, 6)}...${user.walletAddress.slice(-4)}`
              : 'Wallet'}
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <Link
            href="/account"
            className="px-3 py-2 text-sm bg-gray-800 text-gray-300 rounded-md hover:bg-gray-700 transition-colors"
          >
            Account
          </Link>
          <div className="flex items-center space-x-2 text-sm text-gray-400">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span>Live</span>
          </div>
        </div>
      </div>

      {/* Intelligence statistics - only show when we have data */}
      {!loading && !error && processedData.stats.totalSignals > 0 && (
        <div className="bg-gray-800 rounded-lg p-6 mb-8 grid grid-cols-3 gap-6 text-center">
          <div>
            <div className="text-2xl font-bold text-success">
              {processedData.stats.bullishCount}
            </div>
            <div className="text-sm text-gray-400">Bullish Opportunities</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-error">{processedData.stats.bearishCount}</div>
            <div className="text-sm text-gray-400">Bearish Opportunities</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-info">
              {processedData.stats.bullishPercentage}%
            </div>
            <div className="text-sm text-gray-400">Opportunity Rate</div>
          </div>
        </div>
      )}

      {processedData.isEmpty || processedData.crossovers.length === 0 ? (
        <div className="bg-gray-800 rounded-lg p-8 text-center">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-16 w-16 mx-auto mb-4 text-gray-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="text-xl font-medium mb-2">No insights available</p>
          <p className="text-gray-400">
            Our intelligence system is currently analyzing market movements.
            <br />
            New market insights will appear here when opportunities arise.
          </p>
          <p className="text-gray-500 mt-4 text-sm">
            Insights are generated from multiple timeframes and currency pairs.
          </p>
        </div>
      ) : (
        <VirtualizedCrossoverList
          crossovers={processedData.crossovers}
          onItemClick={handleCrossoverClick}
          height={600}
          itemHeight={200}
          enableVirtualization={true}
        />
      )}
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

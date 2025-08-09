'use client';

import { FeedErrorBoundary } from '@/components/error';
import VirtualizedCrossoverList from '@/components/VirtualizedCrossoverList';
import { useLatestCrossovers } from '@/hooks/api';
import { Crossover } from '@/types';
import { CrossoverSkeleton, FeedStatsSkeleton, LoadingSequence } from '@/components/ui';
import React, { useCallback, useMemo } from 'react';
import ProtectedRoute from '../components/ProtectedRoute';

function SignalsPage() {
  const { data: crossoverData, isLoading: loading, error, refetch } = useLatestCrossovers(20); // Get latest 20 crossovers with polling

  // Memoize expensive data processing
  const processedData = useMemo(() => {
    const crossovers = crossoverData?.crossovers || [];
    const isEmpty = crossoverData?.isEmpty || crossovers.length === 0;

    // Expensive calculations: Sort crossovers and compute statistics
    const sortedCrossovers = [...crossovers].sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );

    const bullishCount = crossovers.filter(c => c.crossoverType === 'BULLISH').length;
    const bearishCount = crossovers.filter(c => c.crossoverType === 'BEARISH').length;
    const totalSignals = crossovers.length;
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
    refetch();
  }, [refetch]);

  const handleCrossoverClick = useCallback((crossover: Crossover) => {
    // Handle crossover item clicks (e.g., show details, navigate to analysis)
    console.log('Crossover clicked:', crossover);
  }, []);

  if (loading) {
    return <LoadingSequence type="trading" />;
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-2xl bg-black min-h-screen">
        <h1 className="text-3xl font-bold mb-6">Latest Forex Signals</h1>
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
          <p className="font-medium mb-2">Error loading signals</p>
          <p className="text-sm">{error?.message || 'An error occurred'}</p>
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
    <div className="container mx-auto px-4 py-8 max-w-2xl bg-black min-h-screen">
      <h1 className="text-3xl font-bold mb-6">Latest MA Crossover Signals</h1>

      {/* Signal statistics - only show when we have data */}
      {!loading && !error && processedData.stats.totalSignals > 0 && (
        <div className="bg-gray-800 rounded-lg p-4 mb-6 grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-green-500">
              {processedData.stats.bullishCount}
            </div>
            <div className="text-sm text-gray-400">Bullish</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-red-500">
              {processedData.stats.bearishCount}
            </div>
            <div className="text-sm text-gray-400">Bearish</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-blue-500">
              {processedData.stats.bullishPercentage}%
            </div>
            <div className="text-sm text-gray-400">Bullish Rate</div>
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
          <p className="text-xl font-medium mb-2">No signals available</p>
          <p className="text-gray-400">
            Our system is currently analyzing market movements.
            <br />
            New MA crossover signals will appear here when they occur.
          </p>
          <p className="text-gray-500 mt-4 text-sm">
            Crossovers are monitored across multiple timeframes and pairs.
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
export default function ProtectedSignalsPage(): React.ReactElement {
  return (
    <ProtectedRoute requireSubscription={true}>
      <FeedErrorBoundary>
        <SignalsPage />
      </FeedErrorBoundary>
    </ProtectedRoute>
  );
}

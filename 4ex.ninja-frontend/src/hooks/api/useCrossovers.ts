'use client';

import { getQueryConfig } from '@/lib/queryClient';
import { ApiResponse, Crossover } from '@/types';
import { useQuery, useQueryClient } from '@tanstack/react-query';

// Optimized query keys with better structure to prevent unnecessary refetches
export const crossoverKeys = {
  all: ['crossovers'] as const,
  lists: () => [...crossoverKeys.all, 'list'] as const,
  list: (filters?: CrossoverFilters) => {
    // Sort filters for consistent cache keys
    const sortedFilters = filters
      ? {
          ...filters,
          pairs: filters.pairs?.sort(),
          timeframes: filters.timeframes?.sort(),
          signalTypes: filters.signalTypes?.sort(),
        }
      : undefined;
    return [...crossoverKeys.lists(), sortedFilters] as const;
  },
  pairs: () => [...crossoverKeys.all, 'pairs'] as const,
  latest: (limit: number) => [...crossoverKeys.all, 'latest', limit] as const,
} as const;

interface CrossoverFilters {
  pairs?: string[];
  timeframes?: string[];
  signalTypes?: ('BULLISH' | 'BEARISH')[];
  limit?: number;
  offset?: number;
  startDate?: string;
  endDate?: string;
}

interface CrossoverResponse extends ApiResponse {
  crossovers: Crossover[];
  isEmpty: boolean;
  total?: number;
}

// Fetch crossovers with optional filters
const fetchCrossovers = async (filters?: CrossoverFilters): Promise<CrossoverResponse> => {
  const searchParams = new URLSearchParams();

  if (filters) {
    if (filters.pairs?.length) {
      searchParams.append('pairs', filters.pairs.join(','));
    }
    if (filters.timeframes?.length) {
      searchParams.append('timeframes', filters.timeframes.join(','));
    }
    if (filters.signalTypes?.length) {
      searchParams.append('signalTypes', filters.signalTypes.join(','));
    }
    if (filters.limit) {
      searchParams.append('limit', filters.limit.toString());
    }
    if (filters.offset) {
      searchParams.append('offset', filters.offset.toString());
    }
    if (filters.startDate) {
      searchParams.append('startDate', filters.startDate);
    }
    if (filters.endDate) {
      searchParams.append('endDate', filters.endDate);
    }
  }

  const url = `/api/crossovers${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
  const response = await fetch(url);

  if (!response.ok) {
    const errorData: ApiResponse = await response.json().catch(() => ({
      error: 'Failed to fetch crossovers',
      success: false,
    }));
    throw new Error(errorData.error || 'Failed to fetch crossovers');
  }

  const data: CrossoverResponse = await response.json();

  // Ensure we always have the expected structure
  return {
    ...data,
    crossovers: data.crossovers || [],
    isEmpty: data.isEmpty ?? (data.crossovers || []).length === 0,
    success: data.success ?? true,
  };
};

// Hook for fetching crossovers with optimized caching and real-time updates
export const useCrossovers = (
  filters?: CrossoverFilters,
  options?: {
    enablePolling?: boolean;
    pollingInterval?: number;
    refetchOnWindowFocus?: boolean;
    enableBackgroundRefetch?: boolean;
  }
) => {
  const queryClient = useQueryClient();
  const {
    enablePolling = true,
    pollingInterval = 2 * 60 * 1000, // 2 minutes default (reduced from 5)
    refetchOnWindowFocus = false, // Disabled by default for better UX
    enableBackgroundRefetch = false, // Only for specific use cases
  } = options || {};

  // Get optimized config for real-time data
  const realTimeConfig = getQueryConfig('realTime');

  return useQuery({
    queryKey: crossoverKeys.list(filters),
    queryFn: () => fetchCrossovers(filters),

    // Use optimized caching strategy for real-time data
    staleTime: realTimeConfig.staleTime, // 30 seconds
    gcTime: realTimeConfig.gcTime, // 5 minutes

    // Smart polling configuration
    refetchInterval: enablePolling ? pollingInterval : false,
    refetchIntervalInBackground: enableBackgroundRefetch,

    // Optimized refetch behavior
    refetchOnWindowFocus,
    refetchOnReconnect: true,
    refetchOnMount: true,

    // Enhanced error handling with smart retry logic
    retry: (failureCount, error) => {
      // Don't retry on auth errors
      if (error.message.includes('unauthorized') || error.message.includes('forbidden')) {
        return false;
      }
      // Limited retries for server errors
      if (error.message.includes('500') || error.message.includes('503')) {
        return failureCount < 2;
      }
      return failureCount < 3;
    },

    // Retry delay with exponential backoff
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),

    // Optimized data transformation with error boundaries
    select: data => {
      try {
        return {
          ...data,
          crossovers: data.crossovers.map(crossover => ({
            ...crossover,
            timestamp: new Date(crossover.timestamp),
            time: crossover.time ? new Date(crossover.time) : undefined,
          })),
        };
      } catch (error) {
        console.error('Error transforming crossover data:', error);
        return data; // Return original data if transformation fails
      }
    },

    // Implement cache-first strategy with background updates
    placeholderData: previousData => previousData,
  });
};

// Hook for latest crossovers (most recent signals) with optimized polling
export const useLatestCrossovers = (limit: number = 20) => {
  return useCrossovers(
    { limit, offset: 0 },
    {
      enablePolling: true,
      pollingInterval: 1 * 60 * 1000, // 1 minute for latest data
      refetchOnWindowFocus: false, // Avoid excessive refetches
      enableBackgroundRefetch: false, // Only when tab is active
    }
  );
};

// Hook for crossovers with optimistic updates and mutations
export const useCrossoversWithMutations = () => {
  const queryClient = useQueryClient();

  // Optimistic update for new crossover
  const addOptimisticCrossover = (newCrossover: Crossover) => {
    queryClient.setQueryData(crossoverKeys.latest(20), (old: any) => {
      if (!old) return old;
      return {
        ...old,
        crossovers: [newCrossover, ...old.crossovers.slice(0, 19)],
      };
    });
  };

  // Invalidate relevant queries when real data arrives
  const invalidateCrossoverQueries = () => {
    queryClient.invalidateQueries({
      queryKey: crossoverKeys.all,
      exact: false,
    });
  };

  return {
    addOptimisticCrossover,
    invalidateCrossoverQueries,
  };
};

// Hook for crossover pairs (static data) with long-term caching
export const useCrossoverPairs = () => {
  const staticConfig = getQueryConfig('static');

  return useQuery({
    queryKey: crossoverKeys.pairs(),
    queryFn: async () => {
      const response = await fetch('/api/crossovers/pairs');
      if (!response.ok) {
        throw new Error('Failed to fetch crossover pairs');
      }
      return response.json();
    },

    // Long-term caching for static data
    staleTime: staticConfig.staleTime, // 1 hour
    gcTime: staticConfig.gcTime, // 2 hours

    // Minimal refetching for static data
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
    refetchInterval: false,
  });
};

// Hook for crossovers with specific filters
export const useFilteredCrossovers = (filters: CrossoverFilters) => {
  return useCrossovers(filters, {
    enablePolling: false, // Filtered views don't need aggressive polling
    refetchOnWindowFocus: false,
  });
};

// Hook for infinite scroll / pagination
export const usePaginatedCrossovers = (
  filters?: Omit<CrossoverFilters, 'limit' | 'offset'>,
  pageSize: number = 20
) => {
  const queryClient = useQueryClient();

  const fetchPage = async (pageParam: number) => {
    const paginatedFilters: CrossoverFilters = {
      ...filters,
      limit: pageSize,
      offset: pageParam * pageSize,
    };
    return fetchCrossovers(paginatedFilters);
  };

  // For now, return a regular query with pagination support
  // This can be upgraded to useInfiniteQuery if needed
  return {
    fetchPage,
    invalidateAll: () => queryClient.invalidateQueries({ queryKey: crossoverKeys.all }),
  };
};

// Utility hooks for crossover-related actions
export const useCrossoverActions = () => {
  const queryClient = useQueryClient();

  return {
    // Invalidate all crossover queries
    invalidateAll: () => queryClient.invalidateQueries({ queryKey: crossoverKeys.all }),

    // Invalidate specific crossover list
    invalidateList: (filters?: CrossoverFilters) =>
      queryClient.invalidateQueries({ queryKey: crossoverKeys.list(filters) }),

    // Add new crossover to cache (for real-time updates)
    addCrossover: (crossover: Crossover) => {
      queryClient.setQueriesData<CrossoverResponse>(
        { queryKey: crossoverKeys.lists() },
        oldData => {
          if (!oldData) return oldData;

          // Add to beginning of array (most recent first)
          const updatedCrossovers = [crossover, ...oldData.crossovers];

          return {
            ...oldData,
            crossovers: updatedCrossovers,
            isEmpty: false,
            total: oldData.total ? oldData.total + 1 : updatedCrossovers.length,
          };
        }
      );
    },

    // Remove crossover from cache
    removeCrossover: (crossoverId: string) => {
      queryClient.setQueriesData<CrossoverResponse>(
        { queryKey: crossoverKeys.lists() },
        oldData => {
          if (!oldData) return oldData;

          const updatedCrossovers = oldData.crossovers.filter(c => c._id !== crossoverId);

          return {
            ...oldData,
            crossovers: updatedCrossovers,
            isEmpty: updatedCrossovers.length === 0,
            total: oldData.total ? oldData.total - 1 : updatedCrossovers.length,
          };
        }
      );
    },
  };
};

'use client';

import { ApiResponse, Crossover } from '@/types';
import { useQuery, useQueryClient } from '@tanstack/react-query';

// Query keys for crossover-related queries
export const crossoverKeys = {
  all: ['crossovers'] as const,
  lists: () => [...crossoverKeys.all, 'list'] as const,
  list: (filters?: CrossoverFilters) => [...crossoverKeys.lists(), filters] as const,
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

// Hook for fetching crossovers with optional real-time polling
export const useCrossovers = (
  filters?: CrossoverFilters,
  options?: {
    enablePolling?: boolean;
    pollingInterval?: number;
    refetchOnWindowFocus?: boolean;
  }
) => {
  const {
    enablePolling = true,
    pollingInterval = 5 * 60 * 1000, // 5 minutes default
    refetchOnWindowFocus = true,
  } = options || {};

  return useQuery({
    queryKey: crossoverKeys.list(filters),
    queryFn: () => fetchCrossovers(filters),

    // Caching strategy
    staleTime: 1000 * 60 * 2, // 2 minutes - crossovers are relatively fresh data
    gcTime: 1000 * 60 * 10, // 10 minutes

    // Polling for real-time updates
    refetchInterval: enablePolling ? pollingInterval : false,
    refetchIntervalInBackground: enablePolling, // Continue polling in background

    // Refetch behavior
    refetchOnWindowFocus,
    refetchOnReconnect: true,
    refetchOnMount: true,

    // Error handling and retry logic
    retry: (failureCount, error) => {
      // Don't retry on auth errors
      if (error.message.includes('unauthorized') || error.message.includes('forbidden')) {
        return false;
      }
      // Don't retry too many times for server errors
      if (error.message.includes('500') || error.message.includes('503')) {
        return failureCount < 2;
      }
      return failureCount < 3;
    },

    // Retry delay with exponential backoff
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),

    // Transform data to ensure consistency
    select: data => ({
      ...data,
      crossovers: data.crossovers.map(crossover => ({
        ...crossover,
        timestamp: new Date(crossover.timestamp),
        time: crossover.time ? new Date(crossover.time) : undefined,
      })),
    }),
  });
};

// Hook for latest crossovers (most recent signals)
export const useLatestCrossovers = (limit: number = 20) => {
  return useCrossovers(
    { limit, offset: 0 },
    {
      enablePolling: true,
      pollingInterval: 2 * 60 * 1000, // 2 minutes for latest data
      refetchOnWindowFocus: true,
    }
  );
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

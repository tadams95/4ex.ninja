'use client';

import { recordCacheHit } from '@/utils/performance';
import { QueryClient } from '@tanstack/react-query';

// Data type-specific configurations for optimized caching
const DATA_TYPE_CONFIGS = {
  // Real-time data (crossovers, market data)
  realTime: {
    staleTime: 1000 * 30, // 30 seconds - very fresh data needed
    gcTime: 1000 * 60 * 5, // 5 minutes - shorter cache time
    refetchInterval: 1000 * 60 * 2, // 2 minutes background refetch
  },
  // User data (profile, subscription status)
  user: {
    staleTime: 1000 * 60 * 10, // 10 minutes - changes less frequently
    gcTime: 1000 * 60 * 30, // 30 minutes - keep longer
    refetchInterval: false, // No background refetch
  },
  // Static/semi-static data (pairs list, settings)
  static: {
    staleTime: 1000 * 60 * 60, // 1 hour - rarely changes
    gcTime: 1000 * 60 * 60 * 2, // 2 hours - keep even longer
    refetchInterval: false,
  },
  // Authentication data
  auth: {
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
    refetchInterval: false,
  },
} as const;

// Enhanced retry logic with smart error handling
const getRetryConfig = (failureCount: number, error: any) => {
  // Don't retry on authentication errors
  if (error?.message?.includes('401') || error?.message?.includes('unauthorized')) {
    return false;
  }

  // Don't retry on forbidden errors
  if (error?.message?.includes('403') || error?.message?.includes('forbidden')) {
    return false;
  }

  // Limited retries for server errors
  if (error?.message?.includes('500') || error?.message?.includes('503')) {
    return failureCount < 2;
  }

  // Standard retry count for other errors
  return failureCount < 3;
};

// Create a client with optimized configuration and real-time performance monitoring
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Conservative defaults - will be overridden by specific hooks
      staleTime: 1000 * 60 * 5, // 5 minutes default
      gcTime: 1000 * 60 * 10, // 10 minutes default

      // Enhanced retry logic
      retry: getRetryConfig,
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),

      // Optimized refetch behavior
      refetchOnWindowFocus: false, // Prevent excessive refetches
      refetchOnReconnect: true, // Refetch when connection restored
      refetchOnMount: true, // Fresh data on mount

      // Enable background refetching for stale data
      refetchIntervalInBackground: false, // Only refetch when tab is active

      // Network mode for better offline handling
      networkMode: 'online',
    },
    mutations: {
      // Enhanced mutation retry logic
      retry: (failureCount, error) => {
        // Don't retry auth errors
        if (error?.message?.includes('401') || error?.message?.includes('403')) {
          return false;
        }
        return failureCount < 2;
      },
      retryDelay: 1000,

      // Network mode for mutations
      networkMode: 'online',
    },
  },
});

// Cache performance monitoring utility for real-time tracking (1.10.6.3)
export const trackCacheAccess = (queryKey: any, data: any) => {
  const queryKeyString = JSON.stringify(queryKey);
  recordCacheHit(queryKeyString, data !== undefined);
};

// Helper functions to get optimized query options for different data types
export const getQueryConfig = (dataType: keyof typeof DATA_TYPE_CONFIGS) => {
  return DATA_TYPE_CONFIGS[dataType];
};

// Query prefetching utilities for predictable user flows
export const prefetchQueries = {
  // Prefetch user data after login
  afterLogin: async (queryClient: QueryClient, userId: string) => {
    await Promise.allSettled([
      // Prefetch user profile
      queryClient.prefetchQuery({
        queryKey: ['user', 'profile', userId],
        queryFn: () => fetch(`/api/user/profile`).then(res => res.json()),
        ...getQueryConfig('user'),
      }),

      // Prefetch subscription status
      queryClient.prefetchQuery({
        queryKey: ['user', 'subscription', userId],
        queryFn: () => fetch(`/api/user/subscription`).then(res => res.json()),
        ...getQueryConfig('user'),
      }),

      // Prefetch latest crossovers for immediate feed display
      queryClient.prefetchQuery({
        queryKey: ['crossovers', 'list', { limit: 20, offset: 0 }],
        queryFn: () => fetch(`/api/crossovers?limit=20`).then(res => res.json()),
        ...getQueryConfig('realTime'),
      }),
    ]);
  },

  // Prefetch feed data before navigation
  beforeFeedNavigation: async (queryClient: QueryClient) => {
    await Promise.allSettled([
      // Prefetch latest crossovers
      queryClient.prefetchQuery({
        queryKey: ['crossovers', 'list', { limit: 50, offset: 0 }],
        queryFn: () => fetch(`/api/crossovers?limit=50`).then(res => res.json()),
        ...getQueryConfig('realTime'),
      }),

      // Prefetch available pairs for filtering
      queryClient.prefetchQuery({
        queryKey: ['crossovers', 'pairs'],
        queryFn: () => fetch(`/api/crossovers/pairs`).then(res => res.json()),
        ...getQueryConfig('static'),
      }),
    ]);
  },

  // Prefetch account data before navigation
  beforeAccountNavigation: async (queryClient: QueryClient, userId: string) => {
    await Promise.allSettled([
      // Prefetch user profile
      queryClient.prefetchQuery({
        queryKey: ['user', 'profile', userId],
        queryFn: () => fetch(`/api/user/profile`).then(res => res.json()),
        ...getQueryConfig('user'),
      }),

      // Prefetch subscription history
      queryClient.prefetchQuery({
        queryKey: ['user', 'subscription-history', userId],
        queryFn: () => fetch(`/api/user/subscription/history`).then(res => res.json()),
        ...getQueryConfig('user'),
      }),
    ]);
  },
};

// Cache invalidation strategies for real-time data
export const cacheStrategies = {
  // Invalidate crossover data when new data arrives via WebSocket
  invalidateCrossovers: (queryClient: QueryClient) => {
    queryClient.invalidateQueries({
      queryKey: ['crossovers'],
      exact: false, // Invalidate all crossover queries
    });
  },

  // Invalidate user data after subscription changes
  invalidateUserData: (queryClient: QueryClient, userId: string) => {
    queryClient.invalidateQueries({
      queryKey: ['user', 'subscription', userId],
    });
    queryClient.invalidateQueries({
      queryKey: ['user', 'profile', userId],
    });
  },

  // Background refetch for stale subscription data
  backgroundRefreshSubscription: (queryClient: QueryClient, userId: string) => {
    queryClient.refetchQueries({
      queryKey: ['user', 'subscription', userId],
      type: 'active', // Only refetch if query is currently being used
    });
  },
};

// Optimistic update utilities
export const optimisticUpdates = {
  // Optimistic update for subscription status
  updateSubscriptionStatus: (
    queryClient: QueryClient,
    userId: string,
    newStatus: { isSubscribed: boolean; subscriptionEnds?: string }
  ) => {
    queryClient.setQueryData(['user', 'subscription', userId], (old: any) => ({
      ...old,
      ...newStatus,
    }));
  },

  // Optimistic update for user profile
  updateUserProfile: (queryClient: QueryClient, userId: string, updates: Record<string, any>) => {
    queryClient.setQueryData(['user', 'profile', userId], (old: any) => ({
      ...old,
      ...updates,
    }));
  },
};

// Create a separate client factory for testing or different configurations
export const createQueryClient = (overrides?: ConstructorParameters<typeof QueryClient>[0]) => {
  return new QueryClient({
    defaultOptions: {
      ...queryClient.getDefaultOptions(),
      ...overrides?.defaultOptions,
    },
    ...overrides,
  });
};

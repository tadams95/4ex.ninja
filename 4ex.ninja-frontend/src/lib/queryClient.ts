'use client';

import { QueryClient } from '@tanstack/react-query';

// Create a client with proper configuration for our app
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // How long to consider cached data fresh (5 minutes)
      staleTime: 1000 * 60 * 5,
      // How long to keep unused data in cache (10 minutes)
      gcTime: 1000 * 60 * 10,
      // Retry failed requests up to 3 times
      retry: 3,
      // Retry delay with exponential backoff
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
      // Don't refetch on window focus for better UX
      refetchOnWindowFocus: false,
      // Refetch on network reconnect
      refetchOnReconnect: true,
      // Enable background refetching for stale data
      refetchOnMount: true,
    },
    mutations: {
      // Retry failed mutations once
      retry: 1,
      // Retry delay for mutations
      retryDelay: 1000,
    },
  },
});

// Create a separate client factory for testing or different configurations if needed
export const createQueryClient = (overrides?: ConstructorParameters<typeof QueryClient>[0]) => {
  return new QueryClient({
    defaultOptions: {
      ...queryClient.getDefaultOptions(),
      ...overrides?.defaultOptions,
    },
    ...overrides,
  });
};

'use client';

import { crossoverKeys } from '@/hooks/api/useCrossovers';
import { getQueryConfig } from '@/lib/queryClient';
import { dehydrate, DehydratedState, HydrationBoundary, QueryClient } from '@tanstack/react-query';
import React, { cache, useEffect, useState } from 'react';

/**
 * Server-side query client factory for SSR optimization
 * Creates a fresh query client for each request to prevent data leakage
 */
export const createServerQueryClient = cache(() => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Longer stale time for SSR since we won't be refetching immediately
        staleTime: 1000 * 60 * 5, // 5 minutes
        gcTime: 1000 * 60 * 10, // 10 minutes

        // Disable refetching for SSR
        refetchOnMount: false,
        refetchOnWindowFocus: false,
        refetchOnReconnect: false,
      },
    },
  });
});

/**
 * Server-side data prefetching utilities
 * Prefetches critical data for SSR to improve initial page load
 */
export const serverPrefetch = {
  // Prefetch homepage data
  homepage: async (queryClient: QueryClient) => {
    try {
      await Promise.allSettled([
        // Prefetch latest crossovers for immediate display
        queryClient.prefetchQuery({
          queryKey: crossoverKeys.latest(10),
          queryFn: async () => {
            // In SSR, use absolute URLs
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';
            const response = await fetch(`${baseUrl}/api/crossovers?limit=10`);
            if (!response.ok) throw new Error('Failed to fetch crossovers');
            return response.json();
          },
          ...getQueryConfig('realTime'),
        }),

        // Prefetch available pairs for filtering
        queryClient.prefetchQuery({
          queryKey: crossoverKeys.pairs(),
          queryFn: async () => {
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';
            const response = await fetch(`${baseUrl}/api/crossovers/pairs`);
            if (!response.ok) throw new Error('Failed to fetch pairs');
            return response.json();
          },
          ...getQueryConfig('static'),
        }),
      ]);
    } catch (error) {
      console.warn('Failed to prefetch homepage data:', error);
    }
  },

  // Prefetch feed page data
  feedPage: async (queryClient: QueryClient) => {
    try {
      await Promise.allSettled([
        // Prefetch more crossovers for feed display
        queryClient.prefetchQuery({
          queryKey: crossoverKeys.list({ limit: 50, offset: 0 }),
          queryFn: async () => {
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';
            const response = await fetch(`${baseUrl}/api/crossovers?limit=50`);
            if (!response.ok) throw new Error('Failed to fetch crossovers');
            return response.json();
          },
          ...getQueryConfig('realTime'),
        }),

        // Prefetch pairs for filtering
        queryClient.prefetchQuery({
          queryKey: crossoverKeys.pairs(),
          queryFn: async () => {
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';
            const response = await fetch(`${baseUrl}/api/crossovers/pairs`);
            if (!response.ok) throw new Error('Failed to fetch pairs');
            return response.json();
          },
          ...getQueryConfig('static'),
        }),
      ]);
    } catch (error) {
      console.warn('Failed to prefetch feed data:', error);
    }
  },

  // Prefetch user-specific data (when authenticated)
  userPage: async (queryClient: QueryClient, userId: string) => {
    try {
      await Promise.allSettled([
        // Prefetch user profile
        queryClient.prefetchQuery({
          queryKey: ['user', 'profile', userId],
          queryFn: async () => {
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';
            const response = await fetch(`${baseUrl}/api/user/profile`, {
              headers: {
                Authorization: `Bearer ${process.env.SERVER_API_TOKEN}`, // Server-side auth
              },
            });
            if (!response.ok) throw new Error('Failed to fetch user profile');
            return response.json();
          },
          ...getQueryConfig('user'),
        }),

        // Prefetch subscription status
        queryClient.prefetchQuery({
          queryKey: ['user', 'subscription', userId],
          queryFn: async () => {
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';
            const response = await fetch(`${baseUrl}/api/user/subscription`, {
              headers: {
                Authorization: `Bearer ${process.env.SERVER_API_TOKEN}`,
              },
            });
            if (!response.ok) throw new Error('Failed to fetch subscription');
            return response.json();
          },
          ...getQueryConfig('user'),
        }),
      ]);
    } catch (error) {
      console.warn('Failed to prefetch user data:', error);
    }
  },
};

/**
 * Dehydration utility for SSR
 * Serializes query state for client-side hydration
 */
export const getDehydratedState = (queryClient: QueryClient) => {
  try {
    return dehydrate(queryClient, {
      shouldDehydrateQuery: query => {
        // Only dehydrate successful queries with data
        return query.state.status === 'success' && query.state.data !== undefined;
      },
    });
  } catch (error) {
    console.warn('Failed to dehydrate query state:', error);
    return undefined;
  }
};

/**
 * Hydration boundary component for client-side hydration
 * Provides the dehydrated state to the client-side query client
 */
interface HydrationWrapperProps {
  dehydratedState?: DehydratedState;
  children: React.ReactNode;
}

export const HydrationWrapper: React.FC<HydrationWrapperProps> = ({
  dehydratedState,
  children,
}) => {
  if (!dehydratedState) {
    return <>{children}</>;
  }

  return <HydrationBoundary state={dehydratedState}>{children}</HydrationBoundary>;
};

/**
 * Hook for client-side hydration status
 * Useful for avoiding hydration mismatches
 */
export const useHydrationStatus = () => {
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  return isHydrated;
};

// Re-export for convenience
export { HydrationBoundary };

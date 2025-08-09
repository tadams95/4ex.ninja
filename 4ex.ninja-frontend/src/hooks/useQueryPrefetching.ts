'use client';

import { getQueryConfig, prefetchQueries } from '@/lib/queryClient';
import { useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';
import { crossoverKeys } from './api/useCrossovers';

/**
 * Hook for managing query prefetching across the application
 * Implements predictable user flow prefetching for better UX
 */
export const useQueryPrefetching = () => {
  const queryClient = useQueryClient();

  // Prefetch data after successful login
  const prefetchAfterLogin = useCallback(
    async (userId: string) => {
      try {
        await prefetchQueries.afterLogin(queryClient, userId);
      } catch (error) {
        console.warn('Failed to prefetch data after login:', error);
      }
    },
    [queryClient]
  );

  // Prefetch feed data before navigation
  const prefetchFeedData = useCallback(async () => {
    try {
      await prefetchQueries.beforeFeedNavigation(queryClient);
    } catch (error) {
      console.warn('Failed to prefetch feed data:', error);
    }
  }, [queryClient]);

  // Prefetch account data before navigation
  const prefetchAccountData = useCallback(
    async (userId: string) => {
      try {
        await prefetchQueries.beforeAccountNavigation(queryClient, userId);
      } catch (error) {
        console.warn('Failed to prefetch account data:', error);
      }
    },
    [queryClient]
  );

  // Smart prefetching based on user behavior patterns
  const smartPrefetch = useCallback(
    async (currentRoute: string, userId?: string) => {
      try {
        switch (currentRoute) {
          case '/login':
          case '/register':
            // Prefetch basic crossovers for immediate feed display after auth
            await queryClient.prefetchQuery({
              queryKey: crossoverKeys.latest(10),
              queryFn: () => fetch('/api/crossovers?limit=10').then(res => res.json()),
              ...getQueryConfig('realTime'),
            });
            break;

          case '/':
          case '/home':
            // From homepage, user likely to visit feed or pricing
            await Promise.allSettled([
              prefetchFeedData(),
              queryClient.prefetchQuery({
                queryKey: ['pricing', 'plans'],
                queryFn: () => fetch('/api/pricing/plans').then(res => res.json()),
                ...getQueryConfig('static'),
              }),
            ]);
            break;

          case '/feed':
            // From feed, user might check account or look at more data
            if (userId) {
              await Promise.allSettled([
                prefetchAccountData(userId),
                queryClient.prefetchQuery({
                  queryKey: crossoverKeys.list({ limit: 100, offset: 50 }),
                  queryFn: () =>
                    fetch('/api/crossovers?limit=100&offset=50').then(res => res.json()),
                  ...getQueryConfig('realTime'),
                }),
              ]);
            }
            break;

          case '/account':
            // From account, user might return to feed
            await prefetchFeedData();
            break;

          default:
            // No specific prefetching for unknown routes
            break;
        }
      } catch (error) {
        console.warn('Smart prefetch failed:', error);
      }
    },
    [queryClient, prefetchFeedData, prefetchAccountData]
  );

  // Prefetch on hover for instant navigation
  const prefetchOnHover = useCallback(
    async (targetRoute: string, userId?: string) => {
      try {
        switch (targetRoute) {
          case '/feed':
            await prefetchFeedData();
            break;
          case '/account':
            if (userId) await prefetchAccountData(userId);
            break;
          case '/pricing':
            await queryClient.prefetchQuery({
              queryKey: ['pricing', 'plans'],
              queryFn: () => fetch('/api/pricing/plans').then(res => res.json()),
              ...getQueryConfig('static'),
            });
            break;
          default:
            break;
        }
      } catch (error) {
        console.warn('Hover prefetch failed:', error);
      }
    },
    [queryClient, prefetchFeedData, prefetchAccountData]
  );

  // Prefetch critical data for offline capability
  const prefetchCriticalData = useCallback(
    async (userId?: string) => {
      try {
        const criticalQueries = [
          // Latest crossovers for offline viewing
          queryClient.prefetchQuery({
            queryKey: crossoverKeys.latest(50),
            queryFn: () => fetch('/api/crossovers?limit=50').then(res => res.json()),
            ...getQueryConfig('realTime'),
          }),

          // Available pairs for filtering
          queryClient.prefetchQuery({
            queryKey: crossoverKeys.pairs(),
            queryFn: () => fetch('/api/crossovers/pairs').then(res => res.json()),
            ...getQueryConfig('static'),
          }),
        ];

        // Add user data if authenticated
        if (userId) {
          criticalQueries.push(
            queryClient.prefetchQuery({
              queryKey: ['user', 'profile', userId],
              queryFn: () => fetch('/api/user/profile').then(res => res.json()),
              ...getQueryConfig('user'),
            }),
            queryClient.prefetchQuery({
              queryKey: ['user', 'subscription', userId],
              queryFn: () => fetch('/api/user/subscription').then(res => res.json()),
              ...getQueryConfig('user'),
            })
          );
        }

        await Promise.allSettled(criticalQueries);
      } catch (error) {
        console.warn('Failed to prefetch critical data:', error);
      }
    },
    [queryClient]
  );

  return {
    prefetchAfterLogin,
    prefetchFeedData,
    prefetchAccountData,
    smartPrefetch,
    prefetchOnHover,
    prefetchCriticalData,
  };
};

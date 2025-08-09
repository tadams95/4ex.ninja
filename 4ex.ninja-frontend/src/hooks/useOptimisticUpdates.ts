'use client';

import { cacheStrategies, optimisticUpdates } from '@/lib/queryClient';
import { Crossover, User } from '@/types';
import { useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';
import { crossoverKeys } from './api/useCrossovers';

/**
 * Hook for managing optimistic updates and smart cache invalidation
 * Provides better perceived performance through immediate UI updates
 */
export const useOptimisticUpdates = () => {
  const queryClient = useQueryClient();

  // Optimistic update for user profile changes
  const updateProfileOptimistically = useCallback(
    async (userId: string, updates: Partial<User>, mutationFn: () => Promise<User>) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['user', 'profile', userId] });

      // Snapshot the previous value
      const previousProfile = queryClient.getQueryData(['user', 'profile', userId]);

      // Optimistically update to the new value
      optimisticUpdates.updateUserProfile(queryClient, userId, updates);

      try {
        // Perform the actual mutation
        const result = await mutationFn();

        // Update cache with real data
        queryClient.setQueryData(['user', 'profile', userId], result);

        return result;
      } catch (error) {
        // Rollback on error
        queryClient.setQueryData(['user', 'profile', userId], previousProfile);
        throw error;
      }
    },
    [queryClient]
  );

  // Optimistic update for subscription status
  const updateSubscriptionOptimistically = useCallback(
    async (
      userId: string,
      newStatus: { isSubscribed: boolean; subscriptionEnds?: string },
      mutationFn: () => Promise<any>
    ) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['user', 'subscription', userId] });

      // Snapshot the previous value
      const previousSubscription = queryClient.getQueryData(['user', 'subscription', userId]);

      // Optimistically update to the new value
      optimisticUpdates.updateSubscriptionStatus(queryClient, userId, newStatus);

      try {
        // Perform the actual mutation
        const result = await mutationFn();

        // Update cache with real data
        queryClient.setQueryData(['user', 'subscription', userId], result);

        // Invalidate related queries
        cacheStrategies.invalidateUserData(queryClient, userId);

        return result;
      } catch (error) {
        // Rollback on error
        queryClient.setQueryData(['user', 'subscription', userId], previousSubscription);
        throw error;
      }
    },
    [queryClient]
  );

  // Optimistic update for new crossover data (from WebSocket)
  const addCrossoverOptimistically = useCallback(
    (newCrossover: Crossover) => {
      // Update latest crossovers list
      queryClient.setQueryData(crossoverKeys.latest(20), (old: any) => {
        if (!old) return old;

        // Add new crossover to the beginning and maintain limit
        const updatedCrossovers = [newCrossover, ...old.crossovers].slice(0, 20);

        return {
          ...old,
          crossovers: updatedCrossovers,
          isEmpty: false,
        };
      });

      // Update any filtered lists that would include this crossover
      queryClient.setQueriesData({ queryKey: crossoverKeys.lists(), exact: false }, (old: any) => {
        if (!old) return old;

        // Check if this crossover matches any current filters
        // For simplicity, add to all lists - more sophisticated filtering could be added
        return {
          ...old,
          crossovers: [newCrossover, ...old.crossovers],
          isEmpty: false,
        };
      });
    },
    [queryClient]
  );

  // Smart cache invalidation based on data type and user context
  const smartInvalidateQueries = useCallback(
    (dataType: 'crossovers' | 'user' | 'subscription' | 'all', userId?: string) => {
      switch (dataType) {
        case 'crossovers':
          cacheStrategies.invalidateCrossovers(queryClient);
          break;

        case 'user':
        case 'subscription':
          if (userId) {
            cacheStrategies.invalidateUserData(queryClient, userId);
          }
          break;

        case 'all':
          queryClient.invalidateQueries();
          break;
      }
    },
    [queryClient]
  );

  // Background refresh for stale data
  const backgroundRefresh = useCallback(
    (dataType: 'crossovers' | 'subscription', userId?: string) => {
      switch (dataType) {
        case 'crossovers':
          queryClient.refetchQueries({
            queryKey: crossoverKeys.all,
            type: 'active', // Only refetch active queries
          });
          break;

        case 'subscription':
          if (userId) {
            cacheStrategies.backgroundRefreshSubscription(queryClient, userId);
          }
          break;
      }
    },
    [queryClient]
  );

  // Bulk update crossovers (for WebSocket batch updates)
  const bulkUpdateCrossovers = useCallback(
    (crossovers: Crossover[]) => {
      // Update all crossover-related queries
      queryClient.setQueriesData({ queryKey: crossoverKeys.all, exact: false }, (old: any) => {
        if (!old) return old;

        // Merge new crossovers with existing ones, avoiding duplicates
        const existingIds = new Set(old.crossovers.map((c: Crossover) => c._id));
        const newCrossovers = crossovers.filter(c => !existingIds.has(c._id));

        return {
          ...old,
          crossovers: [...newCrossovers, ...old.crossovers],
          isEmpty: false,
        };
      });
    },
    [queryClient]
  );

  // Remove stale data to free up memory
  const cleanupStaleData = useCallback(() => {
    // Remove queries that haven't been used in the last 10 minutes
    queryClient
      .getQueryCache()
      .findAll()
      .forEach(query => {
        const lastUpdated = query.getObserversCount() > 0 ? Date.now() : query.state.dataUpdatedAt;
        const tenMinutesAgo = Date.now() - 10 * 60 * 1000;

        if (lastUpdated < tenMinutesAgo) {
          queryClient.removeQueries({ queryKey: query.queryKey });
        }
      });
  }, [queryClient]);

  // Optimistic update with retry logic
  const optimisticUpdateWithRetry = useCallback(
    async <T>(
      queryKey: unknown[],
      optimisticData: T,
      mutationFn: () => Promise<T>,
      maxRetries: number = 3
    ) => {
      let attempt = 0;

      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey });

      // Snapshot the previous value
      const previousData = queryClient.getQueryData(queryKey);

      // Optimistically update to the new value
      queryClient.setQueryData(queryKey, optimisticData);

      while (attempt < maxRetries) {
        try {
          // Perform the actual mutation
          const result = await mutationFn();

          // Update cache with real data
          queryClient.setQueryData(queryKey, result);

          return result;
        } catch (error) {
          attempt++;

          if (attempt >= maxRetries) {
            // Rollback on final failure
            queryClient.setQueryData(queryKey, previousData);
            throw error;
          }

          // Wait before retry (exponential backoff)
          await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, attempt)));
        }
      }
    },
    [queryClient]
  );

  return {
    updateProfileOptimistically,
    updateSubscriptionOptimistically,
    addCrossoverOptimistically,
    smartInvalidateQueries,
    backgroundRefresh,
    bulkUpdateCrossovers,
    cleanupStaleData,
    optimisticUpdateWithRetry,
  };
};

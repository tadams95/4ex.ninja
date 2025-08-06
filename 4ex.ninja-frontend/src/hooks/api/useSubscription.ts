'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

// Query keys for subscription-related queries
export const subscriptionKeys = {
  all: ['subscription'] as const,
  status: () => [...subscriptionKeys.all, 'status'] as const,
} as const;

interface SubscriptionStatusResponse {
  isActive: boolean;
  subscriptionEnds?: string | null;
  plan?: string;
  error?: string;
}

interface CancelSubscriptionResponse {
  success: boolean;
  message: string;
  error?: string;
}

// Fetch subscription status
const fetchSubscriptionStatus = async (): Promise<SubscriptionStatusResponse> => {
  const response = await fetch('/api/subscription-status');

  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => ({ error: 'Failed to fetch subscription status' }));
    throw new Error(errorData.error || 'Failed to fetch subscription status');
  }

  return response.json();
};

// Cancel subscription
const cancelSubscription = async (): Promise<CancelSubscriptionResponse> => {
  const response = await fetch('/api/cancel-subscription', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => ({ error: 'Failed to cancel subscription' }));
    throw new Error(errorData.error || 'Failed to cancel subscription');
  }

  return response.json();
};

// Hook for fetching subscription status
export const useSubscriptionStatus = () => {
  return useQuery({
    queryKey: subscriptionKeys.status(),
    queryFn: fetchSubscriptionStatus,
    staleTime: 1000 * 60 * 2, // 2 minutes - subscription status doesn't change often
    gcTime: 1000 * 60 * 5, // 5 minutes
    retry: (failureCount, error) => {
      // Don't retry on auth errors
      if (error.message.includes('unauthorized') || error.message.includes('forbidden')) {
        return false;
      }
      return failureCount < 2;
    },
    refetchOnWindowFocus: true, // Refetch when user returns to app
    refetchOnReconnect: true,
  });
};

// Hook for canceling subscription with optimistic updates
export const useCancelSubscription = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: cancelSubscription,

    // Optimistic update - immediately update UI before API call completes
    onMutate: async () => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: subscriptionKeys.status() });

      // Snapshot the previous value
      const previousStatus = queryClient.getQueryData<SubscriptionStatusResponse>(
        subscriptionKeys.status()
      );

      // Optimistically update to cancelled state
      queryClient.setQueryData<SubscriptionStatusResponse>(subscriptionKeys.status(), old => ({
        ...old,
        isActive: false,
        subscriptionEnds: null,
      }));

      // Return context with previous value
      return { previousStatus };
    },

    // On success, update with server response
    onSuccess: data => {
      queryClient.setQueryData<SubscriptionStatusResponse>(subscriptionKeys.status(), old => ({
        ...old,
        isActive: false,
        subscriptionEnds: null,
      }));

      // Invalidate and refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: subscriptionKeys.status() });
    },

    // On error, rollback the optimistic update
    onError: (error, variables, context) => {
      if (context?.previousStatus) {
        queryClient.setQueryData<SubscriptionStatusResponse>(
          subscriptionKeys.status(),
          context.previousStatus
        );
      }
    },

    // Always refetch after mutation settles
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: subscriptionKeys.status() });
    },
  });
};

// Hook for subscription actions and status
export const useSubscription = () => {
  const statusQuery = useSubscriptionStatus();
  const cancelMutation = useCancelSubscription();

  return {
    // Status data
    status: statusQuery.data,
    isSubscribed: statusQuery.data?.isActive ?? false,
    subscriptionEnds: statusQuery.data?.subscriptionEnds
      ? new Date(statusQuery.data.subscriptionEnds)
      : null,
    plan: statusQuery.data?.plan,

    // Loading states
    isLoading: statusQuery.isLoading,
    isCanceling: cancelMutation.isPending,

    // Error states
    error: statusQuery.error?.message || cancelMutation.error?.message || null,

    // Actions
    cancelSubscription: cancelMutation.mutate,
    refetchStatus: statusQuery.refetch,

    // Additional query info
    isStale: statusQuery.isStale,
    isFetching: statusQuery.isFetching,
  };
};

// Utility hook for subscription-related query invalidation
export const useInvalidateSubscription = () => {
  const queryClient = useQueryClient();

  return {
    invalidateStatus: () => queryClient.invalidateQueries({ queryKey: subscriptionKeys.status() }),
    invalidateAll: () => queryClient.invalidateQueries({ queryKey: subscriptionKeys.all }),
  };
};

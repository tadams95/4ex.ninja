'use client';

import { User } from '@/types';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useSession } from 'next-auth/react';
import { useEffect } from 'react';

// Import subscription hook for integration
import { subscriptionKeys, useSubscriptionStatus } from './useSubscription';

// Query keys for auth-related queries
export const authKeys = {
  all: ['auth'] as const,
  session: () => [...authKeys.all, 'session'] as const,
  user: () => [...authKeys.all, 'user'] as const,
} as const;

interface AuthState {
  isAuthenticated: boolean;
  isSubscribed: boolean;
  user: User | null;
  loading: boolean;
  subscriptionEnds: Date | null;
  subscriptionLoading: boolean;
}

// Enhanced hook that combines NextAuth with React Query and subscription data
export const useAuth = (): AuthState => {
  const { data: session, status } = useSession();
  const queryClient = useQueryClient();

  // Get subscription status using our React Query hook
  const subscriptionQuery = useSubscriptionStatus();

  // Sync session data with React Query cache
  useEffect(() => {
    if (session?.user) {
      // Cache the user data from session
      queryClient.setQueryData<User>(authKeys.user(), session.user as User);
    } else {
      // Clear user data when session ends
      queryClient.removeQueries({ queryKey: authKeys.user() });
      queryClient.removeQueries({ queryKey: subscriptionKeys.all });
    }
  }, [session, queryClient]);

  // Determine subscription status
  const isSubscribed = subscriptionQuery.data?.isActive ?? false;
  const subscriptionEnds = subscriptionQuery.data?.subscriptionEnds
    ? new Date(subscriptionQuery.data.subscriptionEnds)
    : null;

  return {
    isAuthenticated: !!session?.user,
    isSubscribed,
    user: (session?.user as User) || null,
    loading: status === 'loading',
    subscriptionEnds,
    subscriptionLoading: subscriptionQuery.isLoading,
  };
};

// Hook for getting just the user data with React Query caching
export const useAuthUser = () => {
  const { data: session, status } = useSession();

  return useQuery({
    queryKey: authKeys.user(),
    queryFn: () => {
      if (!session?.user) {
        throw new Error('No authenticated user');
      }
      return Promise.resolve(session.user as User);
    },
    enabled: !!session?.user,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 10, // 10 minutes
    retry: false, // Don't retry auth failures
  });
};

// Hook for getting session status with React Query caching
export const useAuthSession = () => {
  const { data: session, status } = useSession();

  return useQuery({
    queryKey: authKeys.session(),
    queryFn: () => {
      return Promise.resolve({
        session,
        isAuthenticated: !!session?.user,
        loading: status === 'loading',
      });
    },
    enabled: true,
    staleTime: 1000 * 60 * 2, // 2 minutes
    gcTime: 1000 * 60 * 5, // 5 minutes
    retry: false,
  });
};

// Hook that provides authentication state for components that need subscription info
export const useAuthWithSubscription = () => {
  const auth = useAuth();
  const subscriptionQuery = useSubscriptionStatus();

  return {
    ...auth,
    // Additional subscription-specific data
    subscription: {
      status: subscriptionQuery.data,
      isLoading: subscriptionQuery.isLoading,
      error: subscriptionQuery.error?.message || null,
      refetch: subscriptionQuery.refetch,
    },
  };
};

// Hook for checking if user has specific permissions
export const useAuthPermissions = () => {
  const auth = useAuth();

  return {
    canAccessPremiumFeatures: auth.isAuthenticated && auth.isSubscribed,
    canAccessBasicFeatures: auth.isAuthenticated,
    needsSubscription: auth.isAuthenticated && !auth.isSubscribed,
    needsAuthentication: !auth.isAuthenticated,

    // Helper methods
    requireAuth: () => {
      if (!auth.isAuthenticated) {
        throw new Error('Authentication required');
      }
    },

    requireSubscription: () => {
      if (!auth.isAuthenticated) {
        throw new Error('Authentication required');
      }
      if (!auth.isSubscribed) {
        throw new Error('Active subscription required');
      }
    },
  };
};

// Utility hook for auth-related query invalidation
export const useInvalidateAuth = () => {
  const queryClient = useQueryClient();

  return {
    invalidateSession: () => queryClient.invalidateQueries({ queryKey: authKeys.session() }),
    invalidateUser: () => queryClient.invalidateQueries({ queryKey: authKeys.user() }),
    invalidateAll: () => queryClient.invalidateQueries({ queryKey: authKeys.all }),

    // Also invalidate subscription data when auth changes
    invalidateAuthAndSubscription: () => {
      queryClient.invalidateQueries({ queryKey: authKeys.all });
      queryClient.invalidateQueries({ queryKey: subscriptionKeys.all });
    },
  };
};

// Hook for components that need to react to auth state changes
export const useAuthStateChanges = (
  onAuthChange?: (isAuthenticated: boolean) => void,
  onSubscriptionChange?: (isSubscribed: boolean) => void
) => {
  const auth = useAuth();

  useEffect(() => {
    onAuthChange?.(auth.isAuthenticated);
  }, [auth.isAuthenticated, onAuthChange]);

  useEffect(() => {
    onSubscriptionChange?.(auth.isSubscribed);
  }, [auth.isSubscribed, onSubscriptionChange]);

  return auth;
};

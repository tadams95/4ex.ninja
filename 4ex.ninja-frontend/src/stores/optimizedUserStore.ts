'use client';

import { User } from '@/types';
import { create } from 'zustand';
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

// Sliced interfaces for selective subscriptions
interface AuthSlice {
  isAuthenticated: boolean;
  user: User | null;
  authLoading: boolean;
}

interface SubscriptionSlice {
  isSubscribed: boolean;
  subscriptionEnds: Date | null;
  subscriptionLoading: boolean;
}

interface ProfileSlice {
  profileLoading: boolean;
  profileError: string | null;
}

// Computed values interface
interface ComputedValues {
  // Memoized computed properties
  userDisplayName: string;
  subscriptionStatus: 'active' | 'expired' | 'trial' | 'none';
  subscriptionDaysRemaining: number;
  canAccessPremiumFeatures: boolean;
  hasValidSubscription: boolean;
}

// Main state interface combining slices
interface OptimizedUserState extends AuthSlice, SubscriptionSlice, ProfileSlice {
  // Computed values
  computed: ComputedValues;

  // Slice-specific actions
  auth: {
    setUser: (user: User | null) => void;
    setAuthLoading: (loading: boolean) => void;
    clearAuth: () => void;
  };

  subscription: {
    setSubscriptionStatus: (isSubscribed: boolean, subscriptionEnds?: Date | string | null) => void;
    setSubscriptionLoading: (loading: boolean) => void;
    clearSubscription: () => void;
  };

  profile: {
    updateProfile: (updates: Partial<User>) => void;
    setProfileLoading: (loading: boolean) => void;
    setProfileError: (error: string | null) => void;
    clearProfile: () => void;
  };

  // Global actions
  reset: () => void;
}

// Helper functions for computed values
const computeDisplayName = (user: User | null): string => {
  if (!user) return 'Guest';
  return user.name || user.email || 'User';
};

const computeSubscriptionStatus = (
  isSubscribed: boolean,
  subscriptionEnds: Date | null
): 'active' | 'expired' | 'trial' | 'none' => {
  if (!isSubscribed) return 'none';
  if (!subscriptionEnds) return 'active';

  const now = new Date();
  const endDate = new Date(subscriptionEnds);

  if (endDate > now) {
    // Check if it's a trial (less than 30 days)
    const daysRemaining = Math.ceil((endDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    return daysRemaining <= 30 ? 'trial' : 'active';
  }

  return 'expired';
};

const computeSubscriptionDaysRemaining = (subscriptionEnds: Date | null): number => {
  if (!subscriptionEnds) return 0;

  const now = new Date();
  const endDate = new Date(subscriptionEnds);
  const diffTime = endDate.getTime() - now.getTime();

  return Math.max(0, Math.ceil(diffTime / (1000 * 60 * 60 * 24)));
};

const computeCanAccessPremiumFeatures = (
  isSubscribed: boolean,
  subscriptionEnds: Date | null
): boolean => {
  if (!isSubscribed) return false;
  if (!subscriptionEnds) return true;

  const now = new Date();
  const endDate = new Date(subscriptionEnds);
  return endDate > now;
};

// Initial state
const initialState = {
  // Auth slice
  isAuthenticated: false,
  user: null,
  authLoading: true,

  // Subscription slice
  isSubscribed: false,
  subscriptionEnds: null,
  subscriptionLoading: false,

  // Profile slice
  profileLoading: false,
  profileError: null,
};

// Create optimized store with slicing and computed values
export const useOptimizedUserStore = create<OptimizedUserState>()(
  subscribeWithSelector(
    devtools(
      persist(
        immer((set, get) => ({
          ...initialState,

          // Computed values (memoized)
          computed: {
            get userDisplayName() {
              const state = get();
              return computeDisplayName(state.user);
            },
            get subscriptionStatus() {
              const state = get();
              return computeSubscriptionStatus(state.isSubscribed, state.subscriptionEnds);
            },
            get subscriptionDaysRemaining() {
              const state = get();
              return computeSubscriptionDaysRemaining(state.subscriptionEnds);
            },
            get canAccessPremiumFeatures() {
              const state = get();
              return computeCanAccessPremiumFeatures(state.isSubscribed, state.subscriptionEnds);
            },
            get hasValidSubscription() {
              const state = get();
              return (
                state.isSubscribed &&
                computeCanAccessPremiumFeatures(state.isSubscribed, state.subscriptionEnds)
              );
            },
          },

          // Auth slice actions
          auth: {
            setUser: user =>
              set(state => {
                state.user = user;
                state.isAuthenticated = !!user;
                state.authLoading = false;
              }),

            setAuthLoading: loading =>
              set(state => {
                state.authLoading = loading;
              }),

            clearAuth: () =>
              set(state => {
                state.user = null;
                state.isAuthenticated = false;
                state.authLoading = false;
              }),
          },

          // Subscription slice actions
          subscription: {
            setSubscriptionStatus: (isSubscribed, subscriptionEnds) =>
              set(state => {
                state.isSubscribed = isSubscribed;
                state.subscriptionEnds = subscriptionEnds ? new Date(subscriptionEnds) : null;
                state.subscriptionLoading = false;
              }),

            setSubscriptionLoading: loading =>
              set(state => {
                state.subscriptionLoading = loading;
              }),

            clearSubscription: () =>
              set(state => {
                state.isSubscribed = false;
                state.subscriptionEnds = null;
                state.subscriptionLoading = false;
              }),
          },

          // Profile slice actions
          profile: {
            updateProfile: updates =>
              set(state => {
                if (state.user) {
                  Object.assign(state.user, updates);
                }
                state.profileLoading = false;
                state.profileError = null;
              }),

            setProfileLoading: loading =>
              set(state => {
                state.profileLoading = loading;
              }),

            setProfileError: error =>
              set(state => {
                state.profileError = error;
                state.profileLoading = false;
              }),

            clearProfile: () =>
              set(state => {
                state.profileLoading = false;
                state.profileError = null;
              }),
          },

          // Global reset
          reset: () => set(() => initialState),
        })),
        {
          name: 'optimized-user-store',
          // Optimize persistence by only storing essential data
          partialize: state => ({
            isAuthenticated: state.isAuthenticated,
            user: state.user,
            isSubscribed: state.isSubscribed,
            subscriptionEnds: state.subscriptionEnds,
          }),
        }
      ),
      {
        name: 'optimized-user-store',
      }
    )
  )
);

// Selective subscription hooks for better performance
export const useAuth = () =>
  useOptimizedUserStore(state => ({
    isAuthenticated: state.isAuthenticated,
    user: state.user,
    authLoading: state.authLoading,
    actions: state.auth,
  }));

export const useSubscription = () =>
  useOptimizedUserStore(state => ({
    isSubscribed: state.isSubscribed,
    subscriptionEnds: state.subscriptionEnds,
    subscriptionLoading: state.subscriptionLoading,
    subscriptionStatus: state.computed.subscriptionStatus,
    daysRemaining: state.computed.subscriptionDaysRemaining,
    canAccessPremium: state.computed.canAccessPremiumFeatures,
    hasValidSubscription: state.computed.hasValidSubscription,
    actions: state.subscription,
  }));

export const useProfile = () =>
  useOptimizedUserStore(state => ({
    user: state.user,
    profileLoading: state.profileLoading,
    profileError: state.profileError,
    displayName: state.computed.userDisplayName,
    actions: state.profile,
  }));

// Computed values only hook (for components that only need derived data)
export const useUserComputed = () => useOptimizedUserStore(state => state.computed);

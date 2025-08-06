'use client';

import { User } from '@/types';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

interface UserState {
  // Authentication state
  isAuthenticated: boolean;
  user: User | null;
  authLoading: boolean;

  // Subscription state
  isSubscribed: boolean;
  subscriptionEnds: Date | null;
  subscriptionLoading: boolean;

  // Profile update state
  profileLoading: boolean;
  profileError: string | null;

  // Actions
  setUser: (user: User | null) => void;
  setAuthLoading: (loading: boolean) => void;
  setSubscriptionStatus: (isSubscribed: boolean, subscriptionEnds?: Date | string | null) => void;
  setSubscriptionLoading: (loading: boolean) => void;
  updateProfile: (updates: Partial<User>) => void;
  setProfileLoading: (loading: boolean) => void;
  setProfileError: (error: string | null) => void;
  clearUser: () => void;
  reset: () => void;
}

const initialState = {
  isAuthenticated: false,
  user: null,
  authLoading: true,
  isSubscribed: false,
  subscriptionEnds: null,
  subscriptionLoading: false,
  profileLoading: false,
  profileError: null,
};

export const useUserStore = create<UserState>()(
  devtools(
    persist(
      immer((set, get) => ({
        ...initialState,

        setUser: (user: User | null) =>
          set(state => {
            state.user = user;
            state.isAuthenticated = !!user;

            // Update subscription status from user data if available
            if (user?.subscriptionEnds) {
              const subscriptionEnds = new Date(user.subscriptionEnds);
              state.subscriptionEnds = subscriptionEnds;
              state.isSubscribed = subscriptionEnds > new Date();
            } else {
              state.subscriptionEnds = null;
              state.isSubscribed = false;
            }
          }),

        setAuthLoading: (loading: boolean) =>
          set(state => {
            state.authLoading = loading;
          }),

        setSubscriptionStatus: (isSubscribed: boolean, subscriptionEnds?: Date | string | null) =>
          set(state => {
            state.isSubscribed = isSubscribed;
            state.subscriptionEnds = subscriptionEnds ? new Date(subscriptionEnds) : null;
          }),

        setSubscriptionLoading: (loading: boolean) =>
          set(state => {
            state.subscriptionLoading = loading;
          }),

        updateProfile: (updates: Partial<User>) =>
          set(state => {
            if (state.user) {
              state.user = { ...state.user, ...updates };
            }
          }),

        setProfileLoading: (loading: boolean) =>
          set(state => {
            state.profileLoading = loading;
          }),

        setProfileError: (error: string | null) =>
          set(state => {
            state.profileError = error;
          }),

        clearUser: () =>
          set(state => {
            state.user = null;
            state.isAuthenticated = false;
            state.isSubscribed = false;
            state.subscriptionEnds = null;
            state.profileError = null;
          }),

        reset: () =>
          set(state => {
            Object.assign(state, initialState);
          }),
      })),
      {
        name: 'user-store',
        // Only persist user data and subscription status, not loading states
        partialize: state => ({
          user: state.user,
          isAuthenticated: state.isAuthenticated,
          isSubscribed: state.isSubscribed,
          subscriptionEnds: state.subscriptionEnds,
        }),
      }
    ),
    {
      name: 'user-store',
    }
  )
);

// Selectors for common use cases
export const useUser = () => useUserStore(state => state.user);
export const useIsAuthenticated = () => useUserStore(state => state.isAuthenticated);
export const useIsSubscribed = () => useUserStore(state => state.isSubscribed);
export const useAuthLoading = () => useUserStore(state => state.authLoading);
export const useSubscriptionStatus = () =>
  useUserStore(state => ({
    isSubscribed: state.isSubscribed,
    subscriptionEnds: state.subscriptionEnds,
    loading: state.subscriptionLoading,
  }));
export const useProfileState = () =>
  useUserStore(state => ({
    loading: state.profileLoading,
    error: state.profileError,
  }));

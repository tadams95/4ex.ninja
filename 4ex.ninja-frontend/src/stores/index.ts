// Central export for all Zustand stores
export * from './crossoverStore';
export * from './notificationStore';
export * from './userStore';

// Optimized stores with performance enhancements
export * from './optimizedUserStore';

// Re-export commonly used hooks for convenience
export {
  useAuthLoading,
  useIsAuthenticated,
  useIsSubscribed,
  useProfileState,
  useSubscriptionStatus,
  useUser,
} from './userStore';

// Optimized store hooks for better performance
export { useAuth, useProfile, useSubscription, useUserComputed } from './optimizedUserStore';

export {
  useCrossoverError,
  useCrossoverFilters,
  useCrossoverLoading,
  useCrossoverPagination,
  useCrossoverSorting,
  useCrossovers,
  useFilteredCrossovers,
} from './crossoverStore';

export {
  useApiErrors,
  useBrowserPermission,
  useNotificationSettings,
  useNotificationSettingsState,
  useToastActions,
  useToasts,
} from './notificationStore';

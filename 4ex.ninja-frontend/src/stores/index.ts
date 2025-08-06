// Central export for all Zustand stores
export * from './userStore';
export * from './crossoverStore';
export * from './notificationStore';

// Re-export commonly used hooks for convenience
export {
  useUser,
  useIsAuthenticated,
  useIsSubscribed,
  useAuthLoading,
  useSubscriptionStatus,
  useProfileState,
} from './userStore';

export {
  useCrossovers,
  useCrossoverLoading,
  useCrossoverError,
  useCrossoverFilters,
  useCrossoverSorting,
  useFilteredCrossovers,
  useCrossoverPagination,
} from './crossoverStore';

export {
  useToasts,
  useNotificationSettings,
  useNotificationSettingsState,
  useApiErrors,
  useBrowserPermission,
  useToastActions,
} from './notificationStore';

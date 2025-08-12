// Central export for all API hooks
export * from './useAuth';
export * from './useCrossovers';
export * from './useUserProfile';

// Re-export commonly used hooks for convenience
export { useAuth } from './useAuth';

export {
  useCrossoverActions,
  useCrossovers,
  useFilteredCrossovers,
  useLatestCrossovers,
} from './useCrossovers';

export {
  useProfileManagement,
  useUpdatePassword,
  useUpdateProfile,
  useUserProfile,
} from './useUserProfile';

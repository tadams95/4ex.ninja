'use client';

import { User } from '@/types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

// Query keys for user profile-related queries
export const userProfileKeys = {
  all: ['userProfile'] as const,
  profile: () => [...userProfileKeys.all, 'profile'] as const,
} as const;

interface ProfileUpdateData {
  name?: string;
  email?: string;
  currentPassword?: string;
  newPassword?: string;
  confirmNewPassword?: string;
}

interface ProfileUpdateResponse {
  success: boolean;
  message: string;
  user?: User;
  error?: string;
}

interface PasswordUpdateData {
  currentPassword: string;
  newPassword: string;
  confirmNewPassword: string;
}

// Fetch user profile data
const fetchUserProfile = async (): Promise<User> => {
  const response = await fetch('/api/user-profile');

  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => ({ error: 'Failed to fetch user profile' }));
    throw new Error(errorData.error || 'Failed to fetch user profile');
  }

  const data = await response.json();
  return data.user || data;
};

// Update user profile
const updateUserProfile = async (
  profileData: ProfileUpdateData
): Promise<ProfileUpdateResponse> => {
  const response = await fetch('/api/update-profile', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(profileData),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Failed to update profile' }));
    throw new Error(errorData.error || 'Failed to update profile');
  }

  return response.json();
};

// Update password specifically
const updatePassword = async (passwordData: PasswordUpdateData): Promise<ProfileUpdateResponse> => {
  const response = await fetch('/api/update-password', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(passwordData),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Failed to update password' }));
    throw new Error(errorData.error || 'Failed to update password');
  }

  return response.json();
};

// Hook for fetching user profile
export const useUserProfile = () => {
  return useQuery({
    queryKey: userProfileKeys.profile(),
    queryFn: fetchUserProfile,

    // Caching strategy
    staleTime: 1000 * 60 * 5, // 5 minutes - profile data doesn't change often
    gcTime: 1000 * 60 * 15, // 15 minutes

    // Retry strategy
    retry: (failureCount, error) => {
      // Don't retry on auth errors
      if (error.message.includes('unauthorized') || error.message.includes('forbidden')) {
        return false;
      }
      return failureCount < 2;
    },

    // Refetch behavior
    refetchOnWindowFocus: false, // Profile data doesn't need aggressive refetching
    refetchOnReconnect: true,
  });
};

// Hook for updating user profile with optimistic updates
export const useUpdateProfile = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateUserProfile,

    // Optimistic update
    onMutate: async (newData: ProfileUpdateData) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: userProfileKeys.profile() });

      // Snapshot the previous value
      const previousProfile = queryClient.getQueryData<User>(userProfileKeys.profile());

      // Optimistically update the profile
      queryClient.setQueryData<User>(userProfileKeys.profile(), old => {
        if (!old) return old;

        return {
          ...old,
          name: newData.name ?? old.name,
          email: newData.email ?? old.email,
          updatedAt: new Date().toISOString(),
        };
      });

      // Return context with previous value
      return { previousProfile };
    },

    // On success, update with server response
    onSuccess: data => {
      if (data.user) {
        queryClient.setQueryData<User>(userProfileKeys.profile(), data.user);
      }

      // Invalidate related queries to ensure consistency
      queryClient.invalidateQueries({ queryKey: userProfileKeys.profile() });

      // Also invalidate subscription status since profile updates might affect it
      queryClient.invalidateQueries({ queryKey: ['subscription'] });
    },

    // On error, rollback the optimistic update
    onError: (error, variables, context) => {
      if (context?.previousProfile) {
        queryClient.setQueryData<User>(userProfileKeys.profile(), context.previousProfile);
      }
    },

    // Always refetch after mutation settles
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: userProfileKeys.profile() });
    },
  });
};

// Hook for updating password (separate from profile for security)
export const useUpdatePassword = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updatePassword,

    // No optimistic updates for password changes
    onSuccess: data => {
      // Invalidate profile to refetch updated data
      queryClient.invalidateQueries({ queryKey: userProfileKeys.profile() });
    },
  });
};

// Combined hook for profile management
export const useProfileManagement = () => {
  const profileQuery = useUserProfile();
  const updateProfileMutation = useUpdateProfile();
  const updatePasswordMutation = useUpdatePassword();

  return {
    // Profile data
    profile: profileQuery.data,

    // Loading states
    isLoading: profileQuery.isLoading,
    isUpdatingProfile: updateProfileMutation.isPending,
    isUpdatingPassword: updatePasswordMutation.isPending,
    isUpdating: updateProfileMutation.isPending || updatePasswordMutation.isPending,

    // Error states
    profileError: profileQuery.error?.message || null,
    updateError:
      updateProfileMutation.error?.message || updatePasswordMutation.error?.message || null,

    // Success states
    updateSuccess: updateProfileMutation.isSuccess || updatePasswordMutation.isSuccess,

    // Actions
    updateProfile: updateProfileMutation.mutate,
    updatePassword: updatePasswordMutation.mutate,
    refetchProfile: profileQuery.refetch,

    // Reset mutation states
    resetUpdateState: () => {
      updateProfileMutation.reset();
      updatePasswordMutation.reset();
    },

    // Additional query info
    isStale: profileQuery.isStale,
    isFetching: profileQuery.isFetching,
  };
};

// Utility hook for profile-related query invalidation
export const useInvalidateProfile = () => {
  const queryClient = useQueryClient();

  return {
    invalidateProfile: () => queryClient.invalidateQueries({ queryKey: userProfileKeys.profile() }),
    invalidateAll: () => queryClient.invalidateQueries({ queryKey: userProfileKeys.all }),
  };
};

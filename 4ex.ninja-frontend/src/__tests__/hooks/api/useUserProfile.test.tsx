import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import React, { ReactNode } from 'react';
import {
  useProfileManagement,
  userProfileKeys,
  useUpdatePassword,
  useUpdateProfile,
  useUserProfile,
} from '../../../hooks/api/useUserProfile';
import { User } from '../../../types';

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock user data
const mockUserData: User = {
  id: '123',
  email: 'test@example.com',
  name: 'Test User',
  isSubscribed: true,
  subscriptionEnds: new Date('2024-12-31'),
};

const mockSuccessResponse = {
  success: true,
  user: mockUserData,
};

const mockUpdateResponse = {
  success: true,
  message: 'Profile updated successfully',
  user: {
    ...mockUserData,
    name: 'Updated User',
    updatedAt: '2024-01-02T00:00:00Z',
  },
};

// Test wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: Infinity,
      },
      mutations: {
        retry: false,
      },
    },
  });

  const TestWrapper = ({ children }: { children: ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);

  return TestWrapper;
};

describe('useUserProfile', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic functionality', () => {
    it('should fetch user profile successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSuccessResponse),
      });

      const { result } = renderHook(() => useUserProfile(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toEqual(mockUserData);
      expect(result.current.error).toBeNull();
      expect(mockFetch).toHaveBeenCalledWith('/api/user-profile');
    });

    it('should handle API errors correctly', async () => {
      const errorMessage = 'Failed to fetch user profile';
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ error: errorMessage }),
      });

      const { result } = renderHook(() => useUserProfile(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.error).toBeTruthy();
      expect(result.current.error?.message).toBe(errorMessage);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => useUserProfile(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.error).toBeTruthy();
      expect(result.current.error?.message).toBe('Network error');
    });
  });

  describe('Caching strategy', () => {
    it('should use correct query keys', () => {
      const expectedKey = userProfileKeys.profile();
      expect(expectedKey).toEqual(['userProfile', 'profile']);
    });

    it('should cache successful responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSuccessResponse),
      });

      const wrapper = createWrapper();
      const { result: result1 } = renderHook(() => useUserProfile(), { wrapper });

      await waitFor(() => {
        expect(result1.current.isLoading).toBe(false);
      });

      // Second render should use cached data
      const { result: result2 } = renderHook(() => useUserProfile(), { wrapper });

      expect(result2.current.isLoading).toBe(false);
      expect(result2.current.data).toEqual(result1.current.data);
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('should not refetch on window focus by default', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSuccessResponse),
      });

      const { result } = renderHook(() => useUserProfile(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Simulate window focus
      window.dispatchEvent(new Event('focus'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Error handling and retry logic', () => {
    it('should not retry on authorization errors', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ error: 'unauthorized' }),
      });

      const { result } = renderHook(() => useUserProfile(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(result.current.error?.message).toBe('unauthorized');
    });

    it('should retry on server errors with limit', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          json: () => Promise.resolve({ error: 'Server error' }),
        })
        .mockResolvedValueOnce({
          ok: false,
          json: () => Promise.resolve({ error: 'Server error' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockSuccessResponse),
        });

      const { result } = renderHook(() => useUserProfile(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(mockFetch).toHaveBeenCalledTimes(3);
      expect(result.current.data).toEqual(mockUserData);
    });
  });
});

describe('useUpdateProfile', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Profile updates', () => {
    it('should update profile successfully', async () => {
      // First setup initial profile data
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSuccessResponse),
      });

      // Then mock the update call
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUpdateResponse),
      });

      const wrapper = createWrapper();
      const { result: profileResult } = renderHook(() => useUserProfile(), { wrapper });
      const { result: updateResult } = renderHook(() => useUpdateProfile(), { wrapper });

      // Wait for initial profile to load
      await waitFor(() => {
        expect(profileResult.current.isLoading).toBe(false);
      });

      // Perform update
      const updateData = { name: 'Updated User' };

      await act(async () => {
        updateResult.current.mutate(updateData);
      });

      await waitFor(() => {
        expect(updateResult.current.isSuccess).toBe(true);
      });

      expect(mockFetch).toHaveBeenCalledWith('/api/update-profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });
    });

    it('should handle update errors', async () => {
      const errorMessage = 'Update failed';
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ error: errorMessage }),
      });

      const { result } = renderHook(() => useUpdateProfile(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate({ name: 'New Name' });
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error?.message).toBe(errorMessage);
    });

    it('should implement optimistic updates', async () => {
      // Setup initial profile
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSuccessResponse),
      });

      const wrapper = createWrapper();
      const { result: profileResult } = renderHook(() => useUserProfile(), { wrapper });
      const { result: updateResult } = renderHook(() => useUpdateProfile(), { wrapper });

      // Wait for initial load
      await waitFor(() => {
        expect(profileResult.current.isLoading).toBe(false);
      });

      expect(profileResult.current.data?.name).toBe('Test User');

      // Mock slow update response
      mockFetch.mockImplementationOnce(
        () =>
          new Promise(resolve =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  json: () => Promise.resolve(mockUpdateResponse),
                }),
              100
            )
          )
      );

      // Trigger optimistic update
      act(() => {
        updateResult.current.mutate({ name: 'Updated User' });
      });

      // Should immediately show optimistic update
      expect(profileResult.current.data?.name).toBe('Updated User');

      // Wait for mutation to complete
      await waitFor(() => {
        expect(updateResult.current.isSuccess).toBe(true);
      });
    });

    it('should rollback optimistic updates on error', async () => {
      // Setup initial profile
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSuccessResponse),
      });

      const wrapper = createWrapper();
      const { result: profileResult } = renderHook(() => useUserProfile(), { wrapper });
      const { result: updateResult } = renderHook(() => useUpdateProfile(), { wrapper });

      await waitFor(() => {
        expect(profileResult.current.isLoading).toBe(false);
      });

      const originalName = profileResult.current.data?.name;

      // Mock failed update
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ error: 'Update failed' }),
      });

      // Trigger update
      await act(async () => {
        updateResult.current.mutate({ name: 'Updated User' });
      });

      await waitFor(() => {
        expect(updateResult.current.isError).toBe(true);
      });

      // Should rollback to original value
      expect(profileResult.current.data?.name).toBe(originalName);
    });
  });
});

describe('useUpdatePassword', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should update password successfully', async () => {
    const passwordResponse = {
      success: true,
      message: 'Password updated successfully',
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(passwordResponse),
    });

    const { result } = renderHook(() => useUpdatePassword(), {
      wrapper: createWrapper(),
    });

    const passwordData = {
      currentPassword: 'oldpass',
      newPassword: 'newpass',
      confirmNewPassword: 'newpass',
    };

    await act(async () => {
      result.current.mutate(passwordData);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockFetch).toHaveBeenCalledWith('/api/update-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(passwordData),
    });
  });

  it('should handle password update errors', async () => {
    const errorMessage = 'Current password is incorrect';
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({ error: errorMessage }),
    });

    const { result } = renderHook(() => useUpdatePassword(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        currentPassword: 'wrong',
        newPassword: 'newpass',
        confirmNewPassword: 'newpass',
      });
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error?.message).toBe(errorMessage);
  });
});

describe('useProfileManagement', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should provide consolidated profile management interface', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockSuccessResponse),
    });

    const { result } = renderHook(() => useProfileManagement(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Should provide all expected properties and methods
    expect(result.current.profile).toEqual(mockUserData);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isUpdatingProfile).toBe(false);
    expect(result.current.isUpdatingPassword).toBe(false);
    expect(result.current.profileError).toBeNull();
    expect(result.current.updateError).toBeNull();

    expect(typeof result.current.updateProfile).toBe('function');
    expect(typeof result.current.updatePassword).toBe('function');
    expect(typeof result.current.refetchProfile).toBe('function');
    expect(typeof result.current.resetUpdateState).toBe('function');
  });

  it('should track update states correctly', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockSuccessResponse),
    });

    const { result } = renderHook(() => useProfileManagement(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Mock slow update
    mockFetch.mockImplementationOnce(
      () =>
        new Promise(resolve =>
          setTimeout(
            () =>
              resolve({
                ok: true,
                json: () => Promise.resolve(mockUpdateResponse),
              }),
            100
          )
        )
    );

    act(() => {
      result.current.updateProfile({ name: 'New Name' });
    });

    // Should show updating state
    expect(result.current.isUpdatingProfile).toBe(true);
    expect(result.current.isUpdating).toBe(true);

    await waitFor(() => {
      expect(result.current.isUpdatingProfile).toBe(false);
    });
  });

  it('should reset mutation states', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockSuccessResponse),
    });

    const { result } = renderHook(() => useProfileManagement(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Trigger successful update
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockUpdateResponse),
    });

    await act(async () => {
      result.current.updateProfile({ name: 'New Name' });
    });

    await waitFor(() => {
      expect(result.current.updateSuccess).toBe(true);
    });

    // Reset state
    act(() => {
      result.current.resetUpdateState();
    });

    expect(result.current.updateSuccess).toBe(false);
  });
});

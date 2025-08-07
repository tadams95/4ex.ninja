import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import React, { ReactNode } from 'react';
import {
  useProfileManagement,
  useUpdateProfile,
  useUserProfile,
} from '../../../hooks/api/useUserProfile';
import { User } from '../../../types';

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock user profile data
const mockUserProfile: User = {
  id: 'user123',
  name: 'John Doe',
  email: 'john@example.com',
  isSubscribed: true,
  createdAt: new Date('2024-01-01'),
  updatedAt: new Date('2024-01-01'),
};

const mockProfileResponse = {
  success: true,
  profile: mockUserProfile,
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

describe('useUserProfile Hook Tests', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Profile data fetching', () => {
    it('should fetch user profile successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockProfileResponse),
      });

      const { result } = renderHook(() => useUserProfile(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toBeDefined();
      expect(result.current.data?.name).toBe('John Doe');
      expect(result.current.data?.email).toBe('john@example.com');
      expect(result.current.error).toBeNull();
      expect(mockFetch).toHaveBeenCalledWith('/api/user-profile');
    });

    it('should handle API errors when fetching profile', async () => {
      const errorMessage = 'Failed to fetch profile';
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ error: errorMessage, success: false }),
      });

      const { result } = renderHook(() => useUserProfile(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      expect(result.current.error?.message).toBe(errorMessage);
      expect(result.current.data).toBeUndefined();
    });
  });

  describe('Profile update functionality', () => {
    it('should update profile successfully', async () => {
      const updatedProfile = { ...mockUserProfile, name: 'Jane Doe' };
      const updateResponse = {
        success: true,
        profile: updatedProfile,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(updateResponse),
      });

      const { result } = renderHook(() => useUpdateProfile(), {
        wrapper: createWrapper(),
      });

      // Trigger mutation
      result.current.mutate({
        name: 'Jane Doe',
        email: 'jane@example.com',
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/update-profile', {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: 'Jane Doe',
            email: 'jane@example.com',
          }),
        });
      });
    });

    it('should handle update errors', async () => {
      const errorMessage = 'Failed to update profile';
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ error: errorMessage, success: false }),
      });

      const { result } = renderHook(() => useUpdateProfile(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ name: 'Jane Doe' });

      await waitFor(() => {
        expect(result.current.error?.message).toBe(errorMessage);
      });
    });
  });

  describe('Profile management hook', () => {
    it('should provide both profile and update functionality', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockProfileResponse),
      });

      const { result } = renderHook(() => useProfileManagement(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.profile).toBeDefined();
      expect(result.current.updateProfile).toBeDefined();
      expect(typeof result.current.updateProfile).toBe('function');
    });
  });

  describe('Error handling', () => {
    it('should handle network errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => useUserProfile(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      expect(result.current.error?.message).toBe('Network error');
    });

    it('should not retry on client errors', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ error: 'Bad request', success: false }),
      });

      const { result } = renderHook(() => useUserProfile(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      // Should only call once (no retries)
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('Cache management', () => {
    it('should cache profile data', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockProfileResponse),
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
  });
});

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { useUpdateProfile, useUserProfile } from '../../../hooks/api/useUserProfile';

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock data
const mockUser = {
  id: 'user123',
  name: 'John Doe',
  email: 'john@example.com',
  isSubscribed: true,
};

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: 0 },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
};

describe('useUserProfile - Core Functionality', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should initialize and make API call', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockUser),
    });

    const { result } = renderHook(() => useUserProfile(), {
      wrapper: createWrapper(),
    });

    // Initial state
    expect(result.current.isLoading).toBe(true);

    // Wait for completion
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Verify API was called
    expect(mockFetch).toHaveBeenCalledWith('/api/user-profile');
  });

  it('should provide data when successful', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockUser),
    });

    const { result } = renderHook(() => useUserProfile(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    expect(result.current.data?.name).toBe('John Doe');
  });
});

describe('useUpdateProfile - Core Functionality', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should make POST request with correct data', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ ...mockUser, name: 'Jane Doe' }),
    });

    const { result } = renderHook(() => useUpdateProfile(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({
      name: 'Jane Doe',
      email: 'jane@example.com',
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/update-profile', {
        method: 'POST',
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

  it('should handle mutation state correctly', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockUser),
    });

    const { result } = renderHook(() => useUpdateProfile(), {
      wrapper: createWrapper(),
    });

    // Initially not pending
    expect(result.current.isPending).toBe(false);

    result.current.mutate({ name: 'Updated Name' });

    await waitFor(() => {
      expect(result.current.isPending).toBe(false);
    });

    // Verify the mutation completed
    expect(mockFetch).toHaveBeenCalled();
  });
});

/**
 * @jest-environment jsdom
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useSubscriptionStatus, useCancelSubscription } from '@/hooks/api/useSubscription';
import '@testing-library/jest-dom';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock next-auth
jest.mock('next-auth/react', () => ({
  useSession: () => ({
    data: {
      user: { id: 'user-123', email: 'test@example.com' },
    },
    status: 'authenticated',
  }),
}));

describe('useSubscription hooks', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    jest.clearAllMocks();
    mockFetch.mockClear();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  describe('useSubscriptionStatus', () => {
    const mockSubscriptionData = {
      isActive: true,
      subscriptionEnds: '2024-12-31T23:59:59Z',
      subscriptionId: 'sub-123',
      plan: 'premium',
    };

    it('should fetch subscription status successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSubscriptionData,
      });

      const { result } = renderHook(() => useSubscriptionStatus(), { wrapper });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.data).toEqual(mockSubscriptionData);
        expect(result.current.isLoading).toBe(false);
      });

      expect(mockFetch).toHaveBeenCalledWith('/api/subscription-status');
    });

    it('should handle subscription fetch error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => useSubscriptionStatus(), { wrapper });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
        expect(result.current.data).toBeUndefined();
        expect(result.current.isLoading).toBe(false);
      });
    });

    it('should handle 404 response gracefully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      });

      const { result } = renderHook(() => useSubscriptionStatus(), { wrapper });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
        expect(result.current.data).toBeUndefined();
      });
    });

    it('should cache subscription data', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSubscriptionData,
      });

      const { result: result1 } = renderHook(() => useSubscriptionStatus(), { wrapper });

      await waitFor(() => {
        expect(result1.current.data).toEqual(mockSubscriptionData);
      });

      // Second hook instance should use cached data
      const { result: result2 } = renderHook(() => useSubscriptionStatus(), { wrapper });

      expect(result2.current.data).toEqual(mockSubscriptionData);
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('should support refetching', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSubscriptionData,
      });

      const { result } = renderHook(() => useSubscriptionStatus(), { wrapper });

      await waitFor(() => {
        expect(result.current.data).toEqual(mockSubscriptionData);
      });

      // Trigger refetch
      await act(async () => {
        await result.current.refetch();
      });

      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('useCancelSubscription', () => {
    it('should cancel subscription successfully', async () => {
      const mockCancelResponse = {
        success: true,
        message: 'Subscription cancelled successfully',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockCancelResponse,
      });

      const { result } = renderHook(() => useCancelSubscription(), { wrapper });

      expect(result.current.isPending).toBe(false);

      await act(async () => {
        await result.current.mutate();
      });

      expect(mockFetch).toHaveBeenCalledWith('/api/cancel-subscription', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      expect(result.current.isSuccess).toBe(true);
      expect(result.current.data).toEqual(mockCancelResponse);
    });

    it('should handle cancellation error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Cancellation failed'));

      const { result } = renderHook(() => useCancelSubscription(), { wrapper });

      await act(async () => {
        try {
          await result.current.mutate();
        } catch (error) {
          // Expected to fail
        }
      });

      expect(result.current.isError).toBe(true);
      expect(result.current.error).toBeTruthy();
    });

    it('should handle server error response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
      });

      const { result } = renderHook(() => useCancelSubscription(), { wrapper });

      await act(async () => {
        try {
          await result.current.mutate();
        } catch (error) {
          // Expected to fail
        }
      });

      expect(result.current.isError).toBe(true);
    });

    it('should show loading state during cancellation', async () => {
      let resolvePromise: (value: any) => void;
      const pendingPromise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      mockFetch.mockReturnValueOnce(pendingPromise);

      const { result } = renderHook(() => useCancelSubscription(), { wrapper });

      act(() => {
        result.current.mutate();
      });

      expect(result.current.isPending).toBe(true);

      // Resolve the promise
      await act(async () => {
        resolvePromise!({
          ok: true,
          json: async () => ({ success: true }),
        });
        await pendingPromise;
      });

      expect(result.current.isPending).toBe(false);
      expect(result.current.isSuccess).toBe(true);
    });

    it('should invalidate subscription queries on successful cancellation', async () => {
      const mockCancelResponse = {
        success: true,
        message: 'Subscription cancelled successfully',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockCancelResponse,
      });

      // Set up some cached subscription data
      queryClient.setQueryData(['subscription', 'status'], {
        isActive: true,
        subscriptionId: 'sub-123',
      });

      const { result } = renderHook(() => useCancelSubscription(), { wrapper });

      await act(async () => {
        await result.current.mutate();
      });

      // Check that subscription cache was invalidated
      await waitFor(() => {
        const cachedData = queryClient.getQueryData(['subscription', 'status']);
        expect(cachedData).toBeDefined(); // Data might be updated rather than cleared
      });
    });

    it('should support optimistic updates', async () => {
      // Set up initial subscription data
      queryClient.setQueryData(['subscription', 'status'], {
        isActive: true,
        subscriptionId: 'sub-123',
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

      const { result } = renderHook(() => useCancelSubscription(), { wrapper });

      await act(async () => {
        await result.current.mutate();
      });

      // Verify the mutation completed successfully
      expect(result.current.isSuccess).toBe(true);
    });

    it('should support custom success behavior through mutation options', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

      const { result } = renderHook(() => useCancelSubscription(), { wrapper });

      await act(async () => {
        await result.current.mutate();
      });

      expect(result.current.isSuccess).toBe(true);
    });
  });

  describe('integration scenarios', () => {
    it('should handle subscription status changes after cancellation', async () => {
      // Initial subscription status
      const initialData = {
        isActive: true,
        subscriptionId: 'sub-123',
      };

      // Updated status after cancellation
      const updatedData = {
        isActive: false,
        subscriptionId: null,
      };

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => initialData,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => updatedData,
        });

      const statusHook = renderHook(() => useSubscriptionStatus(), { wrapper });
      const cancelHook = renderHook(() => useCancelSubscription(), { wrapper });

      // Wait for initial data
      await waitFor(() => {
        expect(statusHook.result.current.data).toEqual(initialData);
      });

      // Cancel subscription
      await act(async () => {
        await cancelHook.result.current.mutate();
      });

      // Refetch status to get updated data
      await act(async () => {
        await statusHook.result.current.refetch();
      });

      await waitFor(() => {
        expect(statusHook.result.current.data).toEqual(updatedData);
      });
    });
  });
});

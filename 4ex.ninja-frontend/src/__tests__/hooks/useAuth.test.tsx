/**
 * @jest-environment jsdom
 */

import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SessionProvider } from 'next-auth/react';
import '@testing-library/jest-dom';

// Mock next-auth
const mockUseSession = jest.fn();

jest.mock('next-auth/react', () => ({
  useSession: () => mockUseSession(),
  SessionProvider: ({ children }: { children: React.ReactNode }) => children,
}));

// Simple mock for subscription hook
jest.mock('@/hooks/api/useSubscription', () => ({
  useSubscriptionStatus: () => ({
    data: null,
    isLoading: false,
    error: null,
  }),
  subscriptionKeys: {
    all: ['subscription'],
  },
}));

// Import after mocking
import { useAuth } from '@/hooks/api/useAuth';

describe('useAuth', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    jest.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <SessionProvider>
        {children}
      </SessionProvider>
    </QueryClientProvider>
  );

  describe('when user is authenticated', () => {
    const mockSession = {
      user: {
        id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
      },
      expires: '2024-12-31',
    };

    beforeEach(() => {
      mockUseSession.mockReturnValue({
        data: mockSession,
        status: 'authenticated',
      });
    });

    it('should return user data and authenticated status', () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.user).toEqual(mockSession.user);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.loading).toBe(false);
    });

    it('should return subscription defaults when no subscription data', () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isSubscribed).toBe(false);
      expect(result.current.subscriptionEnds).toBeNull();
      expect(result.current.subscriptionLoading).toBe(false);
    });
  });

  describe('when user is not authenticated', () => {
    beforeEach(() => {
      mockUseSession.mockReturnValue({
        data: null,
        status: 'unauthenticated',
      });
    });

    it('should return unauthenticated state', () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.loading).toBe(false);
    });

    it('should return default subscription state', () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isSubscribed).toBe(false);
      expect(result.current.subscriptionEnds).toBeNull();
    });
  });

  describe('when session is loading', () => {
    beforeEach(() => {
      mockUseSession.mockReturnValue({
        data: null,
        status: 'loading',
      });
    });

    it('should return loading state', () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.loading).toBe(true);
    });
  });
});

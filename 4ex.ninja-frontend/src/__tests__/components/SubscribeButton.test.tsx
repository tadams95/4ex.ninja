/**
 * @jest-environment jsdom
 */

import SubscribeButton from '@/app/components/SubscribeButton';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { SessionProvider } from 'next-auth/react';

// Mock next/navigation
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock next-auth
const mockUseSession = jest.fn();
jest.mock('next-auth/react', () => ({
  useSession: () => mockUseSession(),
  SessionProvider: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock useAuth hook
const mockUseAuth = jest.fn();
jest.mock('@/hooks/api', () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock error boundary - simple mock that just renders children
jest.mock('@/components/error', () => ({
  SubscribeButtonErrorBoundary: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="subscribe-button-error-boundary">{children}</div>
  ),
}));

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('SubscribeButton', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    jest.clearAllMocks();
    mockPush.mockClear();
    mockFetch.mockClear();
  });

  const TestWrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <SessionProvider>{children}</SessionProvider>
    </QueryClientProvider>
  );

  describe('when user is not authenticated', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        loading: false,
      });
    });

    it('should show sign in button', async () => {
      render(
        <TestWrapper>
          <SubscribeButton />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Sign In')).toBeInTheDocument();
      });
    });

    it('should navigate to login on click', async () => {
      render(
        <TestWrapper>
          <SubscribeButton />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Sign In')).toBeInTheDocument();
      });

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(mockPush).toHaveBeenCalledWith('/login');
    });

    it('should be wrapped in error boundary', () => {
      render(
        <TestWrapper>
          <SubscribeButton />
        </TestWrapper>
      );

      expect(screen.getByTestId('subscribe-button-error-boundary')).toBeInTheDocument();
    });
  });

  describe('when user is authenticated but not subscribed', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        loading: false,
      });

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ isSubscribed: false }),
      });
    });

    it('should show trial button after checking subscription status', async () => {
      render(
        <TestWrapper>
          <SubscribeButton />
        </TestWrapper>
      );

      // Initially loading
      expect(screen.getByText('Loading...')).toBeInTheDocument();

      // After subscription check
      await waitFor(() => {
        expect(screen.getByText('Start 1-Month Free Trial')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith('/api/subscription-status');
    });

    it('should navigate to register on click', async () => {
      render(
        <TestWrapper>
          <SubscribeButton />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Start 1-Month Free Trial')).toBeInTheDocument();
      });

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(mockPush).toHaveBeenCalledWith('/register');
    });

    it('should handle subscription check error gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      render(
        <TestWrapper>
          <SubscribeButton />
        </TestWrapper>
      );

      // Should still show the trial button even on error
      await waitFor(() => {
        expect(screen.getByText('Start 1-Month Free Trial')).toBeInTheDocument();
      });
    });

    it('should handle failed subscription status response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      render(
        <TestWrapper>
          <SubscribeButton />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Start 1-Month Free Trial')).toBeInTheDocument();
      });
    });
  });

  describe('when user is subscribed', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        loading: false,
      });

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ isSubscribed: true }),
      });
    });

    it('should show go to feed button', async () => {
      render(
        <TestWrapper>
          <SubscribeButton />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Go to Feed')).toBeInTheDocument();
      });
    });

    it('should navigate to feed on click', async () => {
      render(
        <TestWrapper>
          <SubscribeButton />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Go to Feed')).toBeInTheDocument();
      });

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(mockPush).toHaveBeenCalledWith('/feed');
    });
  });

  describe('loading states', () => {
    it('should show loading state when auth is loading', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        loading: true,
      });

      render(
        <TestWrapper>
          <SubscribeButton />
        </TestWrapper>
      );

      expect(screen.getByText('Loading...')).toBeInTheDocument();
      expect(screen.getByRole('button')).toBeDisabled();
    });

    it('should show loading state while checking subscription', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        loading: false,
      });

      // Never resolve the fetch to simulate loading
      mockFetch.mockReturnValue(new Promise(() => {}));

      render(
        <TestWrapper>
          <SubscribeButton />
        </TestWrapper>
      );

      expect(screen.getByText('Loading...')).toBeInTheDocument();
      expect(screen.getByRole('button')).toBeDisabled();
    });

    it('should show loading state when button is clicked', async () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        loading: false,
      });

      render(
        <TestWrapper>
          <SubscribeButton />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Sign In')).toBeInTheDocument();
      });

      const button = screen.getByRole('button');
      fireEvent.click(button);

      // Button text changes to loading immediately after click
      expect(screen.getByText('Loading...')).toBeInTheDocument();
      expect(button).toBeDisabled();
    });
  });

  describe('button styling', () => {
    it('should have correct CSS classes', async () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        loading: false,
      });

      render(
        <TestWrapper>
          <SubscribeButton />
        </TestWrapper>
      );

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-green-700');
      expect(button).toHaveClass('hover:bg-green-900');
      expect(button).toHaveClass('text-white');
      expect(button).toHaveClass('font-bold');
      expect(button).toHaveClass('py-2');
      expect(button).toHaveClass('px-4');
      expect(button).toHaveClass('rounded');
    });
  });

  describe('accessibility', () => {
    it('should be keyboard accessible', async () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        loading: false,
      });

      render(
        <TestWrapper>
          <SubscribeButton />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Sign In')).toBeInTheDocument();
      });

      const button = screen.getByRole('button');

      // Should be focusable
      button.focus();
      expect(button).toHaveFocus();

      // Should respond to keyboard events
      fireEvent.keyDown(button, { key: 'Enter', code: 'Enter' });
      expect(mockPush).toHaveBeenCalledWith('/login');
    });

    it('should be disabled during loading states', async () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        loading: false,
      });

      // Mock slow subscription check
      mockFetch.mockReturnValue(
        new Promise(resolve => {
          setTimeout(
            () =>
              resolve({
                ok: true,
                json: async () => ({ isSubscribed: false }),
              }),
            100
          );
        })
      );

      render(
        <TestWrapper>
          <SubscribeButton />
        </TestWrapper>
      );

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();

      // Should become enabled after loading
      await waitFor(() => {
        expect(button).not.toBeDisabled();
      });
    });
  });

  describe('error boundary integration', () => {
    it('should render error boundary wrapper', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        loading: false,
      });

      render(
        <TestWrapper>
          <SubscribeButton />
        </TestWrapper>
      );

      expect(screen.getByTestId('subscribe-button-error-boundary')).toBeInTheDocument();
    });
  });
});

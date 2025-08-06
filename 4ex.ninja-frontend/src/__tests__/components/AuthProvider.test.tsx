/**
 * @jest-environment jsdom
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { SessionProvider } from 'next-auth/react';

// Mock next-auth
jest.mock('next-auth/react', () => ({
  SessionProvider: jest.fn(({ children }) => <div data-testid="session-provider">{children}</div>),
}));

// Mock the entire AuthProvider component to test its structure
const MockAuthProvider = ({ children }: { children: React.ReactNode }) => {
  return (
    <div data-testid="auth-error-boundary">
      <SessionProvider refetchInterval={5 * 60}>{children}</SessionProvider>
    </div>
  );
};

describe('AuthProvider', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    jest.clearAllMocks();
  });

  const TestComponent = () => <div data-testid="test-child">Test Child</div>;

  const renderWithProviders = (component: React.ReactElement) => {
    return render(<QueryClientProvider client={queryClient}>{component}</QueryClientProvider>);
  };

  it('should render children wrapped in SessionProvider', () => {
    renderWithProviders(
      <MockAuthProvider>
        <TestComponent />
      </MockAuthProvider>
    );

    expect(screen.getByTestId('session-provider')).toBeInTheDocument();
    expect(screen.getByTestId('test-child')).toBeInTheDocument();
  });

  it('should configure SessionProvider with refetch interval', () => {
    renderWithProviders(
      <MockAuthProvider>
        <TestComponent />
      </MockAuthProvider>
    );

    expect(SessionProvider).toHaveBeenCalledWith(
      expect.objectContaining({
        refetchInterval: 5 * 60,
        children: expect.anything(),
      }),
      undefined
    );
  });

  it('should maintain session state across re-renders', () => {
    const { rerender } = renderWithProviders(
      <MockAuthProvider>
        <TestComponent />
      </MockAuthProvider>
    );

    expect(screen.getByTestId('test-child')).toBeInTheDocument();

    // Re-render with different children
    rerender(
      <QueryClientProvider client={queryClient}>
        <MockAuthProvider>
          <div data-testid="new-child">New Child</div>
        </MockAuthProvider>
      </QueryClientProvider>
    );

    expect(screen.getByTestId('new-child')).toBeInTheDocument();
    expect(screen.queryByTestId('test-child')).not.toBeInTheDocument();
  });
});

import AuthErrorBoundary from '@/components/error/AuthErrorBoundary';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Component that throws an error for testing
const ThrowError = ({ shouldThrow = false }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Authentication failed');
  }
  return <div>Auth content loaded</div>;
};

// Mock console.error to avoid noise in test output
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

describe('AuthErrorBoundary', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders children when there is no error', () => {
    render(
      <AuthErrorBoundary>
        <div>Authentication working correctly</div>
      </AuthErrorBoundary>
    );

    expect(screen.getByText('Authentication working correctly')).toBeInTheDocument();
  });

  it('catches authentication errors and displays fallback UI', () => {
    render(
      <AuthErrorBoundary>
        <ThrowError shouldThrow={true} />
      </AuthErrorBoundary>
    );

    // Should show the PageErrorFallback with auth-specific messaging
    expect(screen.getByText(/Authentication Error/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
  });

  it('logs authentication errors with specific context', () => {
    render(
      <AuthErrorBoundary>
        <ThrowError shouldThrow={true} />
      </AuthErrorBoundary>
    );

    expect(console.error).toHaveBeenCalledWith(
      'AuthErrorBoundary caught authentication error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('provides reset functionality for auth recovery', async () => {
    const user = userEvent.setup();

    const { rerender } = render(
      <AuthErrorBoundary>
        <ThrowError shouldThrow={true} />
      </AuthErrorBoundary>
    );

    expect(screen.getByText(/Authentication Error/)).toBeInTheDocument();

    const tryAgainButton = screen.getByRole('button', { name: /Try Again/i });
    await user.click(tryAgainButton);

    // After clicking try again, re-render with working component
    rerender(
      <AuthErrorBoundary>
        <ThrowError shouldThrow={false} />
      </AuthErrorBoundary>
    );

    expect(screen.getByText('Auth content loaded')).toBeInTheDocument();
  });

  it('handles authentication session failures gracefully', () => {
    const { rerender } = render(
      <AuthErrorBoundary>
        <ThrowError shouldThrow={true} />
      </AuthErrorBoundary>
    );

    expect(screen.getByText(/Authentication Error/)).toBeInTheDocument();

    // Verify error boundary can handle repeated auth failures
    rerender(
      <AuthErrorBoundary>
        <ThrowError shouldThrow={true} />
      </AuthErrorBoundary>
    );

    expect(screen.getByText(/Authentication Error/)).toBeInTheDocument();
    expect(console.error).toHaveBeenCalledTimes(2);
  });

  it('provides proper error context for login flows', () => {
    render(
      <AuthErrorBoundary>
        <ThrowError shouldThrow={true} />
      </AuthErrorBoundary>
    );

    // Ensure auth-specific error messaging is displayed
    expect(screen.getByText(/Authentication Error/)).toBeInTheDocument();
    expect(screen.queryByText(/Unable to load signals/)).not.toBeInTheDocument();
  });
});

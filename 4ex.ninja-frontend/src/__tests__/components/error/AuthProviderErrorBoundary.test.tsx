import AuthProviderErrorBoundary from '@/components/error/AuthProviderErrorBoundary';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Component that throws an error for testing
const ThrowError = ({ shouldThrow = false }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Auth provider initialization failed');
  }
  return <div>Auth provider working</div>;
};

// Mock console.error to avoid noise in test output
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

describe('AuthProviderErrorBoundary', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders children when there is no error', () => {
    render(
      <AuthProviderErrorBoundary>
        <div>Auth provider initialized successfully</div>
      </AuthProviderErrorBoundary>
    );

    expect(screen.getByText('Auth provider initialized successfully')).toBeInTheDocument();
  });

  it('catches auth provider errors and displays fallback UI', () => {
    render(
      <AuthProviderErrorBoundary>
        <ThrowError shouldThrow={true} />
      </AuthProviderErrorBoundary>
    );

    // Should show component-specific error fallback
    expect(screen.getByText(/Authentication Service Error/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument();
  });

  it('logs auth provider errors with component context', () => {
    render(
      <AuthProviderErrorBoundary>
        <ThrowError shouldThrow={true} />
      </AuthProviderErrorBoundary>
    );

    expect(console.error).toHaveBeenCalledWith(
      'AuthProviderErrorBoundary caught error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('provides retry functionality for auth provider recovery', async () => {
    const user = userEvent.setup();

    const { rerender } = render(
      <AuthProviderErrorBoundary>
        <ThrowError shouldThrow={true} />
      </AuthProviderErrorBoundary>
    );

    expect(screen.getByText(/Authentication Service Error/)).toBeInTheDocument();

    const retryButton = screen.getByRole('button', { name: /Retry/i });
    await user.click(retryButton);

    // After clicking retry, re-render with working component
    rerender(
      <AuthProviderErrorBoundary>
        <ThrowError shouldThrow={false} />
      </AuthProviderErrorBoundary>
    );

    expect(screen.getByText('Auth provider working')).toBeInTheDocument();
  });

  it('handles auth provider initialization failures', () => {
    render(
      <AuthProviderErrorBoundary>
        <ThrowError shouldThrow={true} />
      </AuthProviderErrorBoundary>
    );

    expect(screen.getByText(/Authentication Service Error/)).toBeInTheDocument();
    expect(console.error).toHaveBeenCalledWith(
      'AuthProviderErrorBoundary caught error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('maintains component-level error isolation', () => {
    render(
      <AuthProviderErrorBoundary>
        <ThrowError shouldThrow={true} />
      </AuthProviderErrorBoundary>
    );

    // Ensure component-specific error messaging
    expect(screen.getByText(/Authentication Service Error/)).toBeInTheDocument();
    expect(screen.queryByText(/Pricing Error/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Account Error/)).not.toBeInTheDocument();
  });
});

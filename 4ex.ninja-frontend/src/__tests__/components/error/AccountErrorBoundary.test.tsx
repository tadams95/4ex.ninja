import AccountErrorBoundary from '@/components/error/AccountErrorBoundary';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Component that throws an error for testing
const ThrowError = ({ shouldThrow = false }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Account data loading failed');
  }
  return <div>Account content loaded</div>;
};

// Mock console.error to avoid noise in test output
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

describe('AccountErrorBoundary', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders children when there is no error', () => {
    render(
      <AccountErrorBoundary>
        <div>Account page working correctly</div>
      </AccountErrorBoundary>
    );

    expect(screen.getByText('Account page working correctly')).toBeInTheDocument();
  });

  it('catches account errors and displays fallback UI', () => {
    render(
      <AccountErrorBoundary>
        <ThrowError shouldThrow={true} />
      </AccountErrorBoundary>
    );

    // Should show the PageErrorFallback with account-specific messaging
    expect(screen.getByText('Account Management Error')).toBeInTheDocument();
    expect(screen.getByText(/Unable to load your account information/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
  });

  it('logs account errors with specific context', () => {
    render(
      <AccountErrorBoundary>
        <ThrowError shouldThrow={true} />
      </AccountErrorBoundary>
    );

    expect(console.error).toHaveBeenCalledWith(
      'AccountErrorBoundary caught subscription management error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('provides reset functionality for account recovery', async () => {
    const user = userEvent.setup();

    const { rerender } = render(
      <AccountErrorBoundary>
        <ThrowError shouldThrow={true} />
      </AccountErrorBoundary>
    );

    expect(screen.getByText('Account Management Error')).toBeInTheDocument();

    const tryAgainButton = screen.getByRole('button', { name: /Try Again/i });
    await user.click(tryAgainButton);

    // After clicking try again, re-render with working component
    rerender(
      <AccountErrorBoundary>
        <ThrowError shouldThrow={false} />
      </AccountErrorBoundary>
    );

    expect(screen.getByText('Account content loaded')).toBeInTheDocument();
  });

  it('handles account data loading failures', () => {
    render(
      <AccountErrorBoundary>
        <ThrowError shouldThrow={true} />
      </AccountErrorBoundary>
    );

    expect(screen.getByText('Account Management Error')).toBeInTheDocument();
    expect(console.error).toHaveBeenCalledWith(
      'AccountErrorBoundary caught subscription management error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('maintains proper isolation from other error boundaries', () => {
    render(
      <AccountErrorBoundary>
        <ThrowError shouldThrow={true} />
      </AccountErrorBoundary>
    );

    // Ensure account-specific error messaging is displayed
    expect(screen.getByText('Account Management Error')).toBeInTheDocument();
    expect(screen.queryByText(/Authentication Error/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Unable to load signals/)).not.toBeInTheDocument();
  });
});

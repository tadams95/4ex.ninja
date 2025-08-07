import ProtectedRouteErrorBoundary from '@/components/error/ProtectedRouteErrorBoundary';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Component that throws an error for testing
const ThrowError = ({ shouldThrow = false }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Protected route validation failed');
  }
  return <div>Protected content accessible</div>;
};

// Mock console.error to avoid noise in test output
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

describe('ProtectedRouteErrorBoundary', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders children when there is no error', () => {
    render(
      <ProtectedRouteErrorBoundary>
        <div>Protected route working correctly</div>
      </ProtectedRouteErrorBoundary>
    );

    expect(screen.getByText('Protected route working correctly')).toBeInTheDocument();
  });

  it('catches route protection errors and displays fallback UI', () => {
    render(
      <ProtectedRouteErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ProtectedRouteErrorBoundary>
    );

    // Should show route protection specific error
    expect(screen.getByText(/Access Error/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Retry Access/i })).toBeInTheDocument();
  });

  it('logs route protection errors with context', () => {
    render(
      <ProtectedRouteErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ProtectedRouteErrorBoundary>
    );

    expect(console.error).toHaveBeenCalledWith(
      'ProtectedRouteErrorBoundary caught error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('provides retry access functionality', async () => {
    const user = userEvent.setup();

    const { rerender } = render(
      <ProtectedRouteErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ProtectedRouteErrorBoundary>
    );

    expect(screen.getByText(/Access Error/)).toBeInTheDocument();

    const retryButton = screen.getByRole('button', { name: /Retry Access/i });
    await user.click(retryButton);

    // After clicking retry, re-render with working component
    rerender(
      <ProtectedRouteErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ProtectedRouteErrorBoundary>
    );

    expect(screen.getByText('Protected content accessible')).toBeInTheDocument();
  });

  it('handles authorization failures gracefully', () => {
    render(
      <ProtectedRouteErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ProtectedRouteErrorBoundary>
    );

    expect(screen.getByText(/Access Error/)).toBeInTheDocument();
    expect(console.error).toHaveBeenCalledWith(
      'ProtectedRouteErrorBoundary caught error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('provides appropriate messaging for access control', () => {
    render(
      <ProtectedRouteErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ProtectedRouteErrorBoundary>
    );

    // Should show access-specific messaging
    expect(screen.getByText(/Access Error/)).toBeInTheDocument();
    expect(screen.queryByText(/Navigation Error/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Authentication Service Error/)).not.toBeInTheDocument();
  });

  it('maintains route security context during errors', () => {
    render(
      <ProtectedRouteErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ProtectedRouteErrorBoundary>
    );

    // Verify error boundary doesn't expose protected content
    expect(screen.getByText(/Access Error/)).toBeInTheDocument();
    expect(screen.queryByText('Protected content accessible')).not.toBeInTheDocument();
  });
});

import GlobalErrorBoundary from '@/components/error/GlobalErrorBoundary';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Component that throws an error for testing
const ThrowError = ({ shouldThrow = false }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error message');
  }
  return <div>No error</div>;
};

// Mock console.error to avoid noise in test output
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

describe('GlobalErrorBoundary', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders children when there is no error', () => {
    render(
      <GlobalErrorBoundary>
        <div>Test content</div>
      </GlobalErrorBoundary>
    );

    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('catches errors and displays fallback UI', () => {
    render(
      <GlobalErrorBoundary>
        <ThrowError shouldThrow={true} />
      </GlobalErrorBoundary>
    );

    expect(screen.getByText('Oops!')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText(/We encountered an unexpected error/)).toBeInTheDocument();
  });

  it('displays custom fallback when provided', () => {
    const customFallback = <div>Custom error message</div>;

    render(
      <GlobalErrorBoundary fallback={customFallback}>
        <ThrowError shouldThrow={true} />
      </GlobalErrorBoundary>
    );

    expect(screen.getByText('Custom error message')).toBeInTheDocument();
    expect(screen.queryByText('Oops!')).not.toBeInTheDocument();
  });

  it('provides try again functionality', async () => {
    const user = userEvent.setup();

    const { rerender } = render(
      <GlobalErrorBoundary>
        <ThrowError shouldThrow={true} />
      </GlobalErrorBoundary>
    );

    expect(screen.getByText('Oops!')).toBeInTheDocument();

    const tryAgainButton = screen.getByRole('button', { name: 'Try Again' });
    await user.click(tryAgainButton);

    // After clicking try again, re-render with non-throwing component
    rerender(
      <GlobalErrorBoundary>
        <ThrowError shouldThrow={false} />
      </GlobalErrorBoundary>
    );

    expect(screen.getByText('No error')).toBeInTheDocument();
    expect(screen.queryByText('Oops!')).not.toBeInTheDocument();
  });

  it('provides refresh page functionality', async () => {
    const user = userEvent.setup();

    // Mock window.location.reload
    const mockReload = jest.fn();
    Object.defineProperty(window, 'location', {
      value: { reload: mockReload },
      writable: true,
    });

    render(
      <GlobalErrorBoundary>
        <ThrowError shouldThrow={true} />
      </GlobalErrorBoundary>
    );

    const refreshButton = screen.getByRole('button', { name: 'Refresh Page' });
    await user.click(refreshButton);

    expect(mockReload).toHaveBeenCalledTimes(1);
  });

  it('logs errors to console', () => {
    render(
      <GlobalErrorBoundary>
        <ThrowError shouldThrow={true} />
      </GlobalErrorBoundary>
    );

    expect(console.error).toHaveBeenCalledWith(
      'GlobalErrorBoundary caught an error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('shows error details in development mode', () => {
    // Mock NODE_ENV for this test
    const originalEnv = process.env;
    process.env = { ...originalEnv, NODE_ENV: 'development' };

    render(
      <GlobalErrorBoundary>
        <ThrowError shouldThrow={true} />
      </GlobalErrorBoundary>
    );

    expect(screen.getByText('Error Details (Development Only)')).toBeInTheDocument();

    // Restore original environment
    process.env = originalEnv;
  });

  it('does not show error details in production mode', () => {
    // Mock NODE_ENV for this test
    const originalEnv = process.env;
    process.env = { ...originalEnv, NODE_ENV: 'production' };

    render(
      <GlobalErrorBoundary>
        <ThrowError shouldThrow={true} />
      </GlobalErrorBoundary>
    );

    expect(screen.queryByText('Error Details (Development Only)')).not.toBeInTheDocument();

    // Restore original environment
    process.env = originalEnv;
  });

  it('maintains error state until reset', () => {
    const { rerender } = render(
      <GlobalErrorBoundary>
        <ThrowError shouldThrow={true} />
      </GlobalErrorBoundary>
    );

    expect(screen.getByText('Oops!')).toBeInTheDocument();

    // Re-render with same error boundary but different children
    rerender(
      <GlobalErrorBoundary>
        <div>New content</div>
      </GlobalErrorBoundary>
    );

    // Should still show error state
    expect(screen.getByText('Oops!')).toBeInTheDocument();
    expect(screen.queryByText('New content')).not.toBeInTheDocument();
  });
});

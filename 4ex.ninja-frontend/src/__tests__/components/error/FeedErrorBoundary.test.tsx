import FeedErrorBoundary from '@/components/error/FeedErrorBoundary';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Component that throws an error for testing
const ThrowError = ({ shouldThrow = false }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Signal loading failed');
  }
  return <div>Feed content loaded</div>;
};

// Mock console.error to avoid noise in test output
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

describe('FeedErrorBoundary', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders children when there is no error', () => {
    render(
      <FeedErrorBoundary>
        <div>Feed working correctly</div>
      </FeedErrorBoundary>
    );

    expect(screen.getByText('Feed working correctly')).toBeInTheDocument();
  });

  it('catches signal loading errors and displays fallback UI', () => {
    render(
      <FeedErrorBoundary>
        <ThrowError shouldThrow={true} />
      </FeedErrorBoundary>
    );

    // Should show the PageErrorFallback with signal-specific messaging
    expect(screen.getByText(/Unable to load signals/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
  });

  it('logs signal loading errors with specific context', () => {
    render(
      <FeedErrorBoundary>
        <ThrowError shouldThrow={true} />
      </FeedErrorBoundary>
    );

    expect(console.error).toHaveBeenCalledWith(
      'FeedErrorBoundary caught signal loading error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('provides reset functionality', async () => {
    const user = userEvent.setup();

    const { rerender } = render(
      <FeedErrorBoundary>
        <ThrowError shouldThrow={true} />
      </FeedErrorBoundary>
    );

    expect(screen.getByText(/Unable to load signals/)).toBeInTheDocument();

    const tryAgainButton = screen.getByRole('button', { name: /Try Again/i });
    await user.click(tryAgainButton);

    // After clicking try again, re-render with working component
    rerender(
      <FeedErrorBoundary>
        <ThrowError shouldThrow={false} />
      </FeedErrorBoundary>
    );

    expect(screen.getByText('Feed content loaded')).toBeInTheDocument();
  });

  it('handles multiple error occurrences', () => {
    const { rerender } = render(
      <FeedErrorBoundary>
        <ThrowError shouldThrow={true} />
      </FeedErrorBoundary>
    );

    expect(screen.getByText(/Unable to load signals/)).toBeInTheDocument();

    // Simulate another error after reset
    rerender(
      <FeedErrorBoundary>
        <ThrowError shouldThrow={true} />
      </FeedErrorBoundary>
    );

    expect(screen.getByText(/Unable to load signals/)).toBeInTheDocument();
    expect(console.error).toHaveBeenCalledTimes(2);
  });

  it('maintains error boundary hierarchy', () => {
    // Test that FeedErrorBoundary can be wrapped by GlobalErrorBoundary
    const GlobalErrorBoundary = ({ children }: { children: React.ReactNode }) => (
      <div data-testid="global-boundary">{children}</div>
    );

    render(
      <GlobalErrorBoundary>
        <FeedErrorBoundary>
          <ThrowError shouldThrow={true} />
        </FeedErrorBoundary>
      </GlobalErrorBoundary>
    );

    expect(screen.getByTestId('global-boundary')).toBeInTheDocument();
    expect(screen.getByText(/Unable to load signals/)).toBeInTheDocument();
  });
});

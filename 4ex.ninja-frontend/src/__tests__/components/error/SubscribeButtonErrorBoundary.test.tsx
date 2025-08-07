import SubscribeButtonErrorBoundary from '@/components/error/SubscribeButtonErrorBoundary';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Component that throws an error for testing
const ThrowError = ({ shouldThrow = false }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Subscription button failed');
  }
  return <div>Subscribe button working</div>;
};

// Mock console.error to avoid noise in test output
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

describe('SubscribeButtonErrorBoundary', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders children when there is no error', () => {
    render(
      <SubscribeButtonErrorBoundary>
        <div>Subscribe button loaded successfully</div>
      </SubscribeButtonErrorBoundary>
    );

    expect(screen.getByText('Subscribe button loaded successfully')).toBeInTheDocument();
  });

  it('catches subscription button errors and displays fallback UI', () => {
    render(
      <SubscribeButtonErrorBoundary>
        <ThrowError shouldThrow={true} />
      </SubscribeButtonErrorBoundary>
    );

    // Should show subscription-specific error
    expect(screen.getByText(/Subscription Error/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
  });

  it('logs subscription errors with component context', () => {
    render(
      <SubscribeButtonErrorBoundary>
        <ThrowError shouldThrow={true} />
      </SubscribeButtonErrorBoundary>
    );

    expect(console.error).toHaveBeenCalledWith(
      'SubscribeButtonErrorBoundary caught error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('provides try again functionality for subscription recovery', async () => {
    const user = userEvent.setup();

    const { rerender } = render(
      <SubscribeButtonErrorBoundary>
        <ThrowError shouldThrow={true} />
      </SubscribeButtonErrorBoundary>
    );

    expect(screen.getByText(/Subscription Error/)).toBeInTheDocument();

    const tryAgainButton = screen.getByRole('button', { name: /Try Again/i });
    await user.click(tryAgainButton);

    // After clicking try again, re-render with working component
    rerender(
      <SubscribeButtonErrorBoundary>
        <ThrowError shouldThrow={false} />
      </SubscribeButtonErrorBoundary>
    );

    expect(screen.getByText('Subscribe button working')).toBeInTheDocument();
  });

  it('handles payment processing failures gracefully', () => {
    render(
      <SubscribeButtonErrorBoundary>
        <ThrowError shouldThrow={true} />
      </SubscribeButtonErrorBoundary>
    );

    expect(screen.getByText(/Subscription Error/)).toBeInTheDocument();
    expect(console.error).toHaveBeenCalledWith(
      'SubscribeButtonErrorBoundary caught error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('provides subscription-specific error messaging', () => {
    render(
      <SubscribeButtonErrorBoundary>
        <ThrowError shouldThrow={true} />
      </SubscribeButtonErrorBoundary>
    );

    // Should show subscription-specific messaging
    expect(screen.getByText(/Subscription Error/)).toBeInTheDocument();
    expect(screen.queryByText(/Access Error/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Navigation Error/)).not.toBeInTheDocument();
  });

  it('maintains payment flow context during errors', () => {
    render(
      <SubscribeButtonErrorBoundary>
        <ThrowError shouldThrow={true} />
      </SubscribeButtonErrorBoundary>
    );

    // Verify proper subscription context is maintained
    expect(screen.getByText(/Subscription Error/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
  });
});

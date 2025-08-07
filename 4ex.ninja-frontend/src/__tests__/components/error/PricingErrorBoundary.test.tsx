import PricingErrorBoundary from '@/components/error/PricingErrorBoundary';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Component that throws an error for testing
const ThrowError = ({ shouldThrow = false }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Pricing data loading failed');
  }
  return <div>Pricing content loaded</div>;
};

// Mock console.error to avoid noise in test output
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

describe('PricingErrorBoundary', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders children when there is no error', () => {
    render(
      <PricingErrorBoundary>
        <div>Pricing page working correctly</div>
      </PricingErrorBoundary>
    );

    expect(screen.getByText('Pricing page working correctly')).toBeInTheDocument();
  });

  it('catches pricing errors and displays fallback UI', () => {
    render(
      <PricingErrorBoundary>
        <ThrowError shouldThrow={true} />
      </PricingErrorBoundary>
    );

    // Should show the PageErrorFallback with pricing-specific messaging
    expect(screen.getByText(/Pricing Error/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
  });

  it('logs pricing errors with specific context', () => {
    render(
      <PricingErrorBoundary>
        <ThrowError shouldThrow={true} />
      </PricingErrorBoundary>
    );

    expect(console.error).toHaveBeenCalledWith(
      'PricingErrorBoundary caught pricing error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('provides reset functionality for pricing recovery', async () => {
    const user = userEvent.setup();

    const { rerender } = render(
      <PricingErrorBoundary>
        <ThrowError shouldThrow={true} />
      </PricingErrorBoundary>
    );

    expect(screen.getByText(/Pricing Error/)).toBeInTheDocument();

    const tryAgainButton = screen.getByRole('button', { name: /Try Again/i });
    await user.click(tryAgainButton);

    // After clicking try again, re-render with working component
    rerender(
      <PricingErrorBoundary>
        <ThrowError shouldThrow={false} />
      </PricingErrorBoundary>
    );

    expect(screen.getByText('Pricing content loaded')).toBeInTheDocument();
  });

  it('handles subscription pricing failures gracefully', () => {
    render(
      <PricingErrorBoundary>
        <ThrowError shouldThrow={true} />
      </PricingErrorBoundary>
    );

    expect(screen.getByText(/Pricing Error/)).toBeInTheDocument();
    expect(console.error).toHaveBeenCalledWith(
      'PricingErrorBoundary caught pricing error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('maintains proper context isolation for pricing flows', () => {
    render(
      <PricingErrorBoundary>
        <ThrowError shouldThrow={true} />
      </PricingErrorBoundary>
    );

    // Ensure pricing-specific error messaging is displayed
    expect(screen.getByText(/Pricing Error/)).toBeInTheDocument();
    expect(screen.queryByText(/Authentication Error/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Account Error/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Unable to load signals/)).not.toBeInTheDocument();
  });
});

import HydrationErrorBoundary from '@/components/error/HydrationErrorBoundary';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Component that throws an error for testing
const ThrowError = ({ shouldThrow = false }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Hydration mismatch detected');
  }
  return <div>Hydration successful</div>;
};

// Mock console.error to avoid noise in test output
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

describe('HydrationErrorBoundary', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders children when there is no error', () => {
    render(
      <HydrationErrorBoundary>
        <div>Application hydrated successfully</div>
      </HydrationErrorBoundary>
    );

    expect(screen.getByText('Application hydrated successfully')).toBeInTheDocument();
  });

  it('catches hydration errors and displays fallback UI', () => {
    render(
      <HydrationErrorBoundary>
        <ThrowError shouldThrow={true} />
      </HydrationErrorBoundary>
    );

    // Should show hydration-specific error
    expect(screen.getByText(/Hydration Error/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /reload page/i })).toBeInTheDocument();
  });

  it('logs hydration errors with specific context', () => {
    render(
      <HydrationErrorBoundary>
        <ThrowError shouldThrow={true} />
      </HydrationErrorBoundary>
    );

    expect(console.error).toHaveBeenCalledWith(
      'HydrationErrorBoundary caught error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('provides reload functionality for hydration recovery', async () => {
    const user = userEvent.setup();

    // Mock window.location.reload
    const mockReload = jest.fn();
    Object.defineProperty(window, 'location', {
      value: { reload: mockReload },
      writable: true,
    });

    render(
      <HydrationErrorBoundary>
        <ThrowError shouldThrow={true} />
      </HydrationErrorBoundary>
    );

    const reloadButton = screen.getByRole('button', { name: /reload page/i });
    await user.click(reloadButton);

    expect(mockReload).toHaveBeenCalledTimes(1);
  });

  it('handles SSR mismatch errors appropriately', () => {
    render(
      <HydrationErrorBoundary>
        <ThrowError shouldThrow={true} />
      </HydrationErrorBoundary>
    );

    expect(screen.getByText(/Hydration Error/i)).toBeInTheDocument();
    expect(screen.getByText(/server and client content/i)).toBeInTheDocument();
  });

  it('provides helpful messaging for hydration issues', () => {
    render(
      <HydrationErrorBoundary>
        <ThrowError shouldThrow={true} />
      </HydrationErrorBoundary>
    );

    // Should explain hydration issues to users
    expect(screen.getByText(/Hydration Error/i)).toBeInTheDocument();
    expect(screen.getByText(/server and client content/i)).toBeInTheDocument();
  });

  it('maintains root layout structure during hydration errors', () => {
    render(
      <HydrationErrorBoundary>
        <ThrowError shouldThrow={true} />
      </HydrationErrorBoundary>
    );

    // Should maintain layout and not break page structure
    const container = screen.getByText(/Hydration Error/i).closest('div');
    expect(container).toBeInTheDocument();
  });

  it('handles multiple hydration error occurrences', () => {
    const { rerender } = render(
      <HydrationErrorBoundary>
        <ThrowError shouldThrow={true} />
      </HydrationErrorBoundary>
    );

    expect(screen.getByText(/Hydration Error/i)).toBeInTheDocument();

    // Simulate another hydration error
    rerender(
      <HydrationErrorBoundary>
        <ThrowError shouldThrow={true} />
      </HydrationErrorBoundary>
    );

    expect(screen.getByText(/Hydration Error/i)).toBeInTheDocument();
    expect(console.error).toHaveBeenCalledTimes(2);
  });
});

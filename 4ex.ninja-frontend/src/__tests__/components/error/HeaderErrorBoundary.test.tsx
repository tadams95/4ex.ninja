import HeaderErrorBoundary from '@/components/error/HeaderErrorBoundary';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Component that throws an error for testing
const ThrowError = ({ shouldThrow = false }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Header component failed');
  }
  return <div>Header working correctly</div>;
};

// Mock console.error to avoid noise in test output
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

describe('HeaderErrorBoundary', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders children when there is no error', () => {
    render(
      <HeaderErrorBoundary>
        <div>Header component loaded successfully</div>
      </HeaderErrorBoundary>
    );

    expect(screen.getByText('Header component loaded successfully')).toBeInTheDocument();
  });

  it('catches header errors and displays fallback UI', () => {
    render(
      <HeaderErrorBoundary>
        <ThrowError shouldThrow={true} />
      </HeaderErrorBoundary>
    );

    // Should show minimal header fallback
    expect(screen.getByText(/Navigation Error/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Reload/i })).toBeInTheDocument();
  });

  it('logs header errors with component context', () => {
    render(
      <HeaderErrorBoundary>
        <ThrowError shouldThrow={true} />
      </HeaderErrorBoundary>
    );

    expect(console.error).toHaveBeenCalledWith(
      'HeaderErrorBoundary caught error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('provides reload functionality for header recovery', async () => {
    const user = userEvent.setup();

    const { rerender } = render(
      <HeaderErrorBoundary>
        <ThrowError shouldThrow={true} />
      </HeaderErrorBoundary>
    );

    expect(screen.getByText(/Navigation Error/)).toBeInTheDocument();

    const reloadButton = screen.getByRole('button', { name: /Reload/i });
    await user.click(reloadButton);

    // After clicking reload, re-render with working component
    rerender(
      <HeaderErrorBoundary>
        <ThrowError shouldThrow={false} />
      </HeaderErrorBoundary>
    );

    expect(screen.getByText('Header working correctly')).toBeInTheDocument();
  });

  it('handles navigation component failures gracefully', () => {
    render(
      <HeaderErrorBoundary>
        <ThrowError shouldThrow={true} />
      </HeaderErrorBoundary>
    );

    expect(screen.getByText(/Navigation Error/)).toBeInTheDocument();
    expect(console.error).toHaveBeenCalledWith(
      'HeaderErrorBoundary caught error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('provides minimal fallback to maintain page structure', () => {
    render(
      <HeaderErrorBoundary>
        <ThrowError shouldThrow={true} />
      </HeaderErrorBoundary>
    );

    // Header errors should not break the entire page
    expect(screen.getByText(/Navigation Error/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Reload/i })).toBeInTheDocument();

    // Should not show full page error messages
    expect(screen.queryByText(/Something went wrong/)).not.toBeInTheDocument();
  });
});

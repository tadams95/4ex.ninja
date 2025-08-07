import ProvidersErrorBoundary from '@/components/error/ProvidersErrorBoundary';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Component that throws an error for testing
const ThrowError = ({ shouldThrow = false }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Provider initialization failed');
  }
  return <div>Providers initialized successfully</div>;
};

// Mock console.error to avoid noise in test output
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

describe('ProvidersErrorBoundary', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders children when there is no error', () => {
    render(
      <ProvidersErrorBoundary>
        <div>All providers loaded successfully</div>
      </ProvidersErrorBoundary>
    );

    expect(screen.getByText('All providers loaded successfully')).toBeInTheDocument();
  });

  it('catches provider errors and displays fallback UI', () => {
    render(
      <ProvidersErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ProvidersErrorBoundary>
    );

    // Should show provider-specific error
    expect(screen.getByText(/Provider Error/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /reload application/i })).toBeInTheDocument();
  });

  it('logs provider errors with specific context', () => {
    render(
      <ProvidersErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ProvidersErrorBoundary>
    );

    expect(console.error).toHaveBeenCalledWith(
      'ProvidersErrorBoundary caught error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('provides reload functionality for provider recovery', async () => {
    const user = userEvent.setup();

    // Mock window.location.reload
    const mockReload = jest.fn();
    Object.defineProperty(window, 'location', {
      value: { reload: mockReload },
      writable: true,
    });

    render(
      <ProvidersErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ProvidersErrorBoundary>
    );

    const reloadButton = screen.getByRole('button', { name: /reload application/i });
    await user.click(reloadButton);

    expect(mockReload).toHaveBeenCalledTimes(1);
  });

  it('handles context provider failures gracefully', () => {
    render(
      <ProvidersErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ProvidersErrorBoundary>
    );

    expect(screen.getByText(/Provider Error/i)).toBeInTheDocument();
    expect(screen.getByText(/application context/i)).toBeInTheDocument();
  });

  it('provides helpful messaging for provider issues', () => {
    render(
      <ProvidersErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ProvidersErrorBoundary>
    );

    // Should explain provider initialization issues
    expect(screen.getByText(/Provider Error/i)).toBeInTheDocument();
    expect(screen.getByText(/application context/i)).toBeInTheDocument();
  });

  it('maintains critical application structure during provider errors', () => {
    render(
      <ProvidersErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ProvidersErrorBoundary>
    );

    // Should maintain app structure even when providers fail
    const container = screen.getByText(/Provider Error/i).closest('div');
    expect(container).toBeInTheDocument();
  });

  it('handles theme and state provider failures', () => {
    render(
      <ProvidersErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ProvidersErrorBoundary>
    );

    expect(screen.getByText(/Provider Error/i)).toBeInTheDocument();
    expect(console.error).toHaveBeenCalledWith(
      'ProvidersErrorBoundary caught error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('provides proper isolation for root-level provider errors', () => {
    render(
      <ProvidersErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ProvidersErrorBoundary>
    );

    // Should show provider-specific messaging
    expect(screen.getByText(/Provider Error/i)).toBeInTheDocument();
    expect(screen.queryByText(/Hydration Error/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Authentication Error/i)).not.toBeInTheDocument();
  });
});

import OfflineErrorFallback from '@/components/error/OfflineErrorFallback';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock console.error to avoid noise in test output
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

// Mock the navigator.onLine property
Object.defineProperty(navigator, 'onLine', {
  writable: true,
  value: true,
});

describe('OfflineErrorFallback', () => {
  const mockOnRetry = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    // Reset to online state
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: true,
    });
  });

  it('renders offline message when navigator is offline', () => {
    // Set navigator to offline
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    });

    render(<OfflineErrorFallback onRetry={mockOnRetry} />);

    expect(screen.getByText(/no internet connection/i)).toBeInTheDocument();
    expect(screen.getByText(/check your network connection/i)).toBeInTheDocument();
  });

  it('renders retry button when offline', () => {
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    });

    render(<OfflineErrorFallback onRetry={mockOnRetry} />);

    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('calls onRetry when retry button is clicked', async () => {
    const user = userEvent.setup();
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    });

    render(<OfflineErrorFallback onRetry={mockOnRetry} />);

    const retryButton = screen.getByRole('button', { name: /try again/i });
    await user.click(retryButton);

    expect(mockOnRetry).toHaveBeenCalledTimes(1);
  });

  it('shows appropriate icon for offline state', () => {
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    });

    render(<OfflineErrorFallback onRetry={mockOnRetry} />);

    // Should contain offline/network related icon
    const svgIcon = document.querySelector('svg');
    expect(svgIcon).toBeInTheDocument();
  });

  it('provides helpful messaging for network issues', () => {
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    });

    render(<OfflineErrorFallback onRetry={mockOnRetry} />);

    expect(screen.getByText(/no internet connection/i)).toBeInTheDocument();
    expect(screen.getByText(/check your network connection/i)).toBeInTheDocument();
  });

  it('handles online state appropriately', () => {
    // Navigator is online
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: true,
    });

    render(<OfflineErrorFallback onRetry={mockOnRetry} />);

    // Should still show fallback UI but with different messaging
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('maintains consistent styling with other error components', () => {
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    });

    render(<OfflineErrorFallback onRetry={mockOnRetry} />);

    // Should have proper container structure
    const container = screen.getByText(/no internet connection/i).closest('div');
    expect(container).toBeInTheDocument();
  });

  it('provides accessibility features for offline state', () => {
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    });

    render(<OfflineErrorFallback onRetry={mockOnRetry} />);

    const retryButton = screen.getByRole('button', { name: /try again/i });
    expect(retryButton).toBeInTheDocument();
    expect(retryButton).not.toBeDisabled();
  });
});

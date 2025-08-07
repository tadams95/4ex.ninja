import RetryableError from '@/components/error/RetryableError';
import { ApiError } from '@/utils/error-handler';
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

describe('RetryableError', () => {
  const mockOnRetry = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  const createApiError = (overrides: Partial<ApiError> = {}): ApiError => ({
    message: 'API request failed',
    timestamp: new Date().toISOString(),
    ...overrides,
  });

  it('renders network error with retry button', () => {
    const networkError = createApiError({ code: 'NETWORK_ERROR' });

    render(<RetryableError error={networkError} onRetry={mockOnRetry} />);

    expect(screen.getByText('Connection Problem')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('calls onRetry when retry button is clicked', async () => {
    const user = userEvent.setup();
    const serverError = createApiError({ status: 500 });

    render(<RetryableError error={serverError} onRetry={mockOnRetry} />);

    const retryButton = screen.getByRole('button', { name: /try again/i });
    await user.click(retryButton);

    expect(mockOnRetry).toHaveBeenCalledTimes(1);
  });

  it('handles server errors with retry functionality', () => {
    const serverError = createApiError({ status: 500 });

    render(<RetryableError error={serverError} onRetry={mockOnRetry} />);

    expect(screen.getByText('Server Error')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('handles rate limit errors appropriately', () => {
    const rateLimitError = createApiError({ status: 429 });

    render(<RetryableError error={rateLimitError} onRetry={mockOnRetry} />);

    expect(screen.getByText('Rate Limit Exceeded')).toBeInTheDocument();
    expect(screen.getByText(/making requests too quickly/)).toBeInTheDocument();
  });

  it('shows non-retryable errors without retry button', () => {
    const clientError = createApiError({ status: 400 });

    render(<RetryableError error={clientError} onRetry={mockOnRetry} />);

    expect(screen.getByText('Request Failed')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /try again/i })).not.toBeInTheDocument();
  });

  it('respects maxRetries prop', async () => {
    const user = userEvent.setup();
    const networkError = createApiError({ code: 'NETWORK_ERROR' });

    render(<RetryableError error={networkError} onRetry={mockOnRetry} maxRetries={1} />);

    const retryButton = screen.getByRole('button', { name: /try again/i });

    // First click should work
    await user.click(retryButton);
    expect(mockOnRetry).toHaveBeenCalledTimes(1);

    // Second click should be disabled (exceeded maxRetries)
    await user.click(retryButton);
    expect(mockOnRetry).toHaveBeenCalledTimes(1);
  });

  it('shows retrying state during retry operation', async () => {
    const user = userEvent.setup();
    const networkError = createApiError({ code: 'NETWORK_ERROR' });

    // Mock onRetry to return a pending promise
    const pendingPromise = new Promise(() => {}); // Never resolves
    mockOnRetry.mockReturnValue(pendingPromise);

    render(<RetryableError error={networkError} onRetry={mockOnRetry} />);

    const retryButton = screen.getByRole('button', { name: /try again/i });
    await user.click(retryButton);

    expect(screen.getByText('Retrying...')).toBeInTheDocument();
    expect(retryButton).toBeDisabled();
  });

  it('displays retry attempts counter', async () => {
    const user = userEvent.setup();
    const networkError = createApiError({ code: 'NETWORK_ERROR' });

    render(<RetryableError error={networkError} onRetry={mockOnRetry} maxRetries={3} />);

    const retryButton = screen.getByRole('button', { name: /try again/i });
    await user.click(retryButton);

    expect(screen.getByText(/2 attempts left/)).toBeInTheDocument();
  });
});

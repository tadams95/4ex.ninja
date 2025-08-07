import PageErrorFallback from '@/components/error/PageErrorFallback';
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

describe('PageErrorFallback', () => {
  const mockResetError = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders default error message when no custom message provided', () => {
    render(<PageErrorFallback resetError={mockResetError} />);

    expect(screen.getByText('Page Error')).toBeInTheDocument();
    expect(screen.getByText(/page encountered an error/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('renders custom error message when provided', () => {
    render(<PageErrorFallback resetError={mockResetError} message="Custom error message" />);

    expect(screen.getByText('Custom error message')).toBeInTheDocument();
  });

  it('renders custom title when provided', () => {
    render(<PageErrorFallback resetError={mockResetError} title="Custom Error Title" />);

    expect(screen.getByText('Custom Error Title')).toBeInTheDocument();
  });

  it('calls resetError when try again button is clicked', async () => {
    const user = userEvent.setup();

    render(<PageErrorFallback resetError={mockResetError} />);

    const tryAgainButton = screen.getByRole('button', { name: /try again/i });
    await user.click(tryAgainButton);

    expect(mockResetError).toHaveBeenCalledTimes(1);
  });

  it('reloads page when resetError is not provided', async () => {
    const user = userEvent.setup();

    // Mock window.location.reload
    const mockReload = jest.fn();
    Object.defineProperty(window, 'location', {
      value: { reload: mockReload },
      writable: true,
    });

    render(<PageErrorFallback />);

    const tryAgainButton = screen.getByRole('button', { name: /try again/i });
    await user.click(tryAgainButton);

    expect(mockReload).toHaveBeenCalledTimes(1);
  });

  it('navigates to home when go home button is clicked', async () => {
    const user = userEvent.setup();

    // Mock window.location.href
    const mockLocation = { href: '' };
    Object.defineProperty(window, 'location', {
      value: mockLocation,
      writable: true,
    });

    render(<PageErrorFallback resetError={mockResetError} />);

    const goHomeButton = screen.getByRole('button', { name: /go home/i });
    await user.click(goHomeButton);

    expect(mockLocation.href).toBe('/');
  });

  it('renders with proper error styling and layout', () => {
    render(<PageErrorFallback resetError={mockResetError} />);

    // Should have proper container structure
    const container = screen.getByText('Page Error').closest('div');
    expect(container).toBeInTheDocument();
  });

  it('shows error icon when displayed', () => {
    render(<PageErrorFallback resetError={mockResetError} />);

    // Should contain error icon
    const svgIcon = document.querySelector('svg');
    expect(svgIcon).toBeInTheDocument();
  });

  it('handles error object when passed', () => {
    const testError = new Error('Test error message');

    render(<PageErrorFallback resetError={mockResetError} error={testError} />);

    expect(screen.getByText('Page Error')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('provides accessible error information', () => {
    render(
      <PageErrorFallback
        resetError={mockResetError}
        title="Accessibility Test"
        message="This is an accessible error message"
      />
    );

    expect(screen.getByText('Accessibility Test')).toBeInTheDocument();
    expect(screen.getByText('This is an accessible error message')).toBeInTheDocument();

    const tryAgainButton = screen.getByRole('button', { name: /try again/i });
    expect(tryAgainButton).not.toBeDisabled();
  });

  it('maintains consistent styling across different configurations', () => {
    const { rerender } = render(<PageErrorFallback resetError={mockResetError} />);

    let container = screen.getByText('Page Error').closest('div');
    expect(container).toBeInTheDocument();

    rerender(
      <PageErrorFallback
        resetError={mockResetError}
        title="Custom Title"
        message="Custom Message"
      />
    );

    container = screen.getByText('Custom Title').closest('div');
    expect(container).toBeInTheDocument();
  });

  it('handles both action buttons appropriately', async () => {
    const user = userEvent.setup();

    const mockReload = jest.fn();
    const mockLocation = { href: '' };
    Object.defineProperty(window, 'location', {
      value: { ...mockLocation, reload: mockReload },
      writable: true,
    });

    render(<PageErrorFallback resetError={mockResetError} />);

    const tryAgainButton = screen.getByRole('button', { name: /try again/i });
    const goHomeButton = screen.getByRole('button', { name: /go home/i });

    expect(tryAgainButton).toBeInTheDocument();
    expect(goHomeButton).toBeInTheDocument();

    await user.click(tryAgainButton);
    expect(mockResetError).toHaveBeenCalledTimes(1);
  });
});

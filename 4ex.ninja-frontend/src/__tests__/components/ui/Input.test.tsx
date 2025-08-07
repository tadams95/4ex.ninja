import { Input } from '@/components/ui/Input';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('Input Component', () => {
  it('renders basic input correctly', () => {
    render(<Input placeholder="Enter text" />);
    const input = screen.getByPlaceholderText('Enter text');
    expect(input).toBeInTheDocument();
    expect(input).toHaveClass('bg-neutral-700');
  });

  it('renders with label when provided', () => {
    render(<Input label="Email Address" />);
    const label = screen.getByText('Email Address');
    const input = screen.getByLabelText('Email Address');

    expect(label).toBeInTheDocument();
    expect(input).toBeInTheDocument();
    expect(label).toHaveAttribute('for', 'email-address');
    expect(input).toHaveAttribute('id', 'email-address');
  });

  it('applies correct variant classes', () => {
    const { rerender } = render(<Input variant="default" data-testid="input" />);
    let input = screen.getByTestId('input');
    expect(input).toHaveClass('rounded-md');

    rerender(<Input variant="rounded" data-testid="input" />);
    input = screen.getByTestId('input');
    expect(input).toHaveClass('rounded-full');
  });

  it('displays error message when error is provided', () => {
    render(<Input label="Email" error="Invalid email address" />);

    const input = screen.getByLabelText('Email');
    const errorMessage = screen.getByText('Invalid email address');

    expect(input).toHaveClass('border-error focus:ring-error');
    expect(errorMessage).toBeInTheDocument();
    expect(errorMessage).toHaveAttribute('role', 'alert');
  });

  it('displays helper text when provided and no error', () => {
    render(<Input label="Password" helperText="Must be at least 8 characters" />);

    const helperText = screen.getByText('Must be at least 8 characters');
    expect(helperText).toBeInTheDocument();
    expect(helperText).toHaveClass('text-neutral-400');
  });

  it('prioritizes error over helper text', () => {
    render(<Input label="Email" error="Invalid email" helperText="Enter your email address" />);

    expect(screen.getByText('Invalid email')).toBeInTheDocument();
    expect(screen.queryByText('Enter your email address')).not.toBeInTheDocument();
  });

  it('handles user input correctly', async () => {
    const handleChange = jest.fn();
    const user = userEvent.setup();

    render(<Input onChange={handleChange} placeholder="Type here" />);
    const input = screen.getByPlaceholderText('Type here');

    await user.type(input, 'Hello World');

    expect(input).toHaveValue('Hello World');
    expect(handleChange).toHaveBeenCalledTimes(11); // One for each character
  });

  it('applies custom className', () => {
    render(<Input className="custom-input" data-testid="input" />);
    const input = screen.getByTestId('input');
    expect(input).toHaveClass('custom-input');
  });

  it('forwards HTML input props correctly', () => {
    render(<Input type="email" required disabled data-testid="email-input" maxLength={50} />);
    const input = screen.getByTestId('email-input');

    expect(input).toHaveAttribute('type', 'email');
    expect(input).toBeRequired();
    expect(input).toBeDisabled();
    expect(input).toHaveAttribute('maxLength', '50');
  });

  it('uses custom id when provided', () => {
    render(<Input label="Custom Field" id="custom-id" />);

    const label = screen.getByText('Custom Field');
    const input = screen.getByLabelText('Custom Field');

    expect(label).toHaveAttribute('for', 'custom-id');
    expect(input).toHaveAttribute('id', 'custom-id');
  });

  it('has proper focus styles', () => {
    render(<Input data-testid="input" />);
    const input = screen.getByTestId('input');

    input.focus();
    expect(input).toHaveFocus();
    expect(input).toHaveClass('focus:ring-primary-500');
    expect(input).toHaveClass('focus:border-primary-500');
  });

  it('applies error styles when error is present', () => {
    render(<Input error="Something went wrong" data-testid="input" />);
    const input = screen.getByTestId('input');

    expect(input).toHaveClass('border-error');
    expect(input).toHaveClass('focus:ring-error');
    expect(input).toHaveClass('focus:border-error');
  });

  it('applies normal border styles when no error', () => {
    render(<Input data-testid="input" />);
    const input = screen.getByTestId('input');

    expect(input).toHaveClass('border-neutral-600');
    expect(input).not.toHaveClass('border-error');
  });

  it('handles controlled input correctly', () => {
    const { rerender } = render(<Input value="initial" readOnly />);
    const input = screen.getByDisplayValue('initial');

    expect(input).toHaveValue('initial');

    rerender(<Input value="updated" readOnly />);
    expect(input).toHaveValue('updated');
  });
});

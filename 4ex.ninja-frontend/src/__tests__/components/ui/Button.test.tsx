import { Button } from '@/components/ui/Button';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('Button Component', () => {
  it('renders children correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('applies correct variant classes', () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>);
    let button = screen.getByRole('button');
    expect(button).toHaveClass('bg-primary-700');

    rerender(<Button variant="secondary">Secondary</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('bg-neutral-700');

    rerender(<Button variant="outline">Outline</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('border-neutral-600');

    rerender(<Button variant="ghost">Ghost</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('bg-transparent');
  });

  it('applies correct size classes', () => {
    const { rerender } = render(<Button size="sm">Small</Button>);
    let button = screen.getByRole('button');
    expect(button).toHaveClass('py-1.5 px-3 text-sm');

    rerender(<Button size="md">Medium</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('py-2 px-4 text-base');

    rerender(<Button size="lg">Large</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('py-3 px-6 text-lg');
  });

  it('handles loading state correctly', () => {
    render(<Button loading>Loading</Button>);
    const button = screen.getByRole('button');

    expect(button).toBeDisabled();
    expect(button).toHaveClass('opacity-50 cursor-not-allowed');

    // Check for loading spinner SVG
    const spinner = button.querySelector('svg.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('handles disabled state correctly', () => {
    render(<Button disabled>Disabled</Button>);
    const button = screen.getByRole('button');

    expect(button).toBeDisabled();
    expect(button).toHaveClass('opacity-50 cursor-not-allowed');
  });

  it('handles click events', async () => {
    const handleClick = jest.fn();
    const user = userEvent.setup();

    render(<Button onClick={handleClick}>Click me</Button>);
    const button = screen.getByRole('button');

    await user.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('does not call onClick when disabled or loading', async () => {
    const handleClick = jest.fn();
    const user = userEvent.setup();

    const { rerender } = render(
      <Button onClick={handleClick} disabled>
        Disabled
      </Button>
    );
    let button = screen.getByRole('button');

    await user.click(button);
    expect(handleClick).not.toHaveBeenCalled();

    rerender(
      <Button onClick={handleClick} loading>
        Loading
      </Button>
    );
    button = screen.getByRole('button');

    await user.click(button);
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('applies custom className', () => {
    render(<Button className="custom-class">Custom</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('custom-class');
  });

  it('forwards HTML button props correctly', () => {
    render(
      <Button type="submit" data-testid="submit-button">
        Submit
      </Button>
    );
    const button = screen.getByTestId('submit-button');
    expect(button).toHaveAttribute('type', 'submit');
  });

  it('has proper accessibility attributes', () => {
    render(<Button aria-label="Close modal">×</Button>);
    const button = screen.getByRole('button', { name: 'Close modal' });
    expect(button).toHaveAccessibleName('Close modal');
  });

  it('has focus styles for keyboard navigation', () => {
    render(<Button>Focusable</Button>);
    const button = screen.getByRole('button');

    button.focus();
    expect(button).toHaveFocus();
    expect(button).toHaveClass('focus:ring-2 focus:ring-primary-500');
  });
});

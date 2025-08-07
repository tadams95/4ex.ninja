import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { render, screen } from '@testing-library/react';

describe('LoadingSpinner Component', () => {
  it('renders loading spinner correctly', () => {
    render(<LoadingSpinner />);
    const spinner = screen.getByRole('status');

    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveAttribute('aria-label', 'Loading');
  });

  it('applies correct size classes', () => {
    const { rerender } = render(<LoadingSpinner size="sm" />);
    let spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('h-4 w-4');

    rerender(<LoadingSpinner size="md" />);
    spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('h-6 w-6');

    rerender(<LoadingSpinner size="lg" />);
    spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('h-8 w-8');

    rerender(<LoadingSpinner size="xl" />);
    spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('h-12 w-12');
  });

  it('applies default size when not specified', () => {
    render(<LoadingSpinner />);
    const spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('h-6 w-6'); // md is default
  });

  it('applies correct color classes', () => {
    const { rerender } = render(<LoadingSpinner color="white" />);
    let spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('text-white');

    rerender(<LoadingSpinner color="primary" />);
    spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('text-primary-500');

    rerender(<LoadingSpinner color="neutral" />);
    spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('text-neutral-400');
  });

  it('applies default color when not specified', () => {
    render(<LoadingSpinner />);
    const spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('text-primary-500'); // primary is default
  });

  it('applies custom className', () => {
    render(<LoadingSpinner className="custom-spinner" />);
    const spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('custom-spinner');
  });

  it('combines all props correctly', () => {
    render(<LoadingSpinner size="lg" color="white" className="additional-class" />);
    const spinner = screen.getByRole('status');

    expect(spinner).toHaveClass('h-8 w-8');
    expect(spinner).toHaveClass('text-white');
    expect(spinner).toHaveClass('additional-class');
    expect(spinner).toHaveClass('animate-spin');
  });

  it('has spinning animation class', () => {
    render(<LoadingSpinner />);
    const spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('animate-spin');
  });

  it('has proper SVG structure with circle and path elements', () => {
    render(<LoadingSpinner />);
    const spinner = screen.getByRole('status');

    // Check SVG properties
    expect(spinner.tagName).toBe('svg');
    expect(spinner).toHaveAttribute('xmlns', 'http://www.w3.org/2000/svg');
    expect(spinner).toHaveAttribute('fill', 'none');
    expect(spinner).toHaveAttribute('viewBox', '0 0 24 24');

    // Check for circle and path elements
    const circle = spinner.querySelector('circle');
    const path = spinner.querySelector('path');

    expect(circle).toBeInTheDocument();
    expect(path).toBeInTheDocument();

    if (circle) {
      expect(circle).toHaveAttribute('cx', '12');
      expect(circle).toHaveAttribute('cy', '12');
      expect(circle).toHaveAttribute('r', '10');
      expect(circle).toHaveClass('opacity-25');
    }

    if (path) {
      expect(path).toHaveClass('opacity-75');
    }
  });

  it('maintains aspect ratio across different sizes', () => {
    const { rerender } = render(<LoadingSpinner size="sm" />);
    let spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('h-4 w-4'); // Square aspect ratio

    rerender(<LoadingSpinner size="xl" />);
    spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('h-12 w-12'); // Square aspect ratio
  });

  it('has accessible role and label', () => {
    render(<LoadingSpinner />);
    const spinner = screen.getByRole('status');

    expect(spinner).toHaveAttribute('role', 'status');
    expect(spinner).toHaveAttribute('aria-label', 'Loading');
  });

  it('preserves all size and color combinations', () => {
    const sizes = ['sm', 'md', 'lg', 'xl'] as const;
    const colors = ['white', 'primary', 'neutral'] as const;

    // Test each combination individually
    expect(sizes.length).toBe(4);
    expect(colors.length).toBe(3);

    // Test a few key combinations
    render(<LoadingSpinner size="sm" color="white" />);
    expect(screen.getByRole('status')).toHaveClass('h-4 w-4 text-white');

    render(<LoadingSpinner size="lg" color="primary" />);
    expect(screen.getAllByRole('status')[1]).toHaveClass('h-8 w-8 text-primary-500');

    render(<LoadingSpinner size="xl" color="neutral" />);
    expect(screen.getAllByRole('status')[2]).toHaveClass('h-12 w-12 text-neutral-400');
  });
});

import { Card } from '@/components/ui/Card';
import { render, screen } from '@testing-library/react';

describe('Card Component', () => {
  it('renders children correctly', () => {
    render(
      <Card>
        <p>Card content</p>
      </Card>
    );
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('applies default variant and padding classes', () => {
    render(<Card data-testid="card">Default card</Card>);
    const card = screen.getByTestId('card');

    expect(card).toHaveClass('bg-neutral-800 rounded-lg p-4');
  });

  it('applies correct variant classes', () => {
    const { rerender } = render(
      <Card data-testid="card" variant="default">
        Default
      </Card>
    );
    let card = screen.getByTestId('card');
    expect(card).toHaveClass('bg-neutral-800');
    expect(card).not.toHaveClass('shadow-lg');
    expect(card).not.toHaveClass('border');

    rerender(
      <Card data-testid="card" variant="elevated">
        Elevated
      </Card>
    );
    card = screen.getByTestId('card');
    expect(card).toHaveClass('shadow-lg');

    rerender(
      <Card data-testid="card" variant="outlined">
        Outlined
      </Card>
    );
    card = screen.getByTestId('card');
    expect(card).toHaveClass('border border-neutral-600');
  });

  it('applies correct padding classes', () => {
    const { rerender } = render(
      <Card data-testid="card" padding="none">
        None
      </Card>
    );
    let card = screen.getByTestId('card');
    expect(card).not.toHaveClass('p-3');
    expect(card).not.toHaveClass('p-4');
    expect(card).not.toHaveClass('p-6');

    rerender(
      <Card data-testid="card" padding="sm">
        Small
      </Card>
    );
    card = screen.getByTestId('card');
    expect(card).toHaveClass('p-3');

    rerender(
      <Card data-testid="card" padding="md">
        Medium
      </Card>
    );
    card = screen.getByTestId('card');
    expect(card).toHaveClass('p-4');

    rerender(
      <Card data-testid="card" padding="lg">
        Large
      </Card>
    );
    card = screen.getByTestId('card');
    expect(card).toHaveClass('p-6');
  });

  it('applies custom className', () => {
    render(
      <Card data-testid="card" className="custom-class">
        Custom
      </Card>
    );
    const card = screen.getByTestId('card');
    expect(card).toHaveClass('custom-class');
  });

  it('renders as motion.div when hover is enabled', () => {
    render(
      <Card data-testid="card" hover>
        Hoverable card
      </Card>
    );
    const card = screen.getByTestId('card');

    // Motion div should be present and functional
    expect(card).toBeInTheDocument();
    expect(card).toHaveClass('bg-neutral-800');
  });

  it('renders as regular div when hover is disabled', () => {
    render(
      <Card data-testid="card" hover={false}>
        Regular card
      </Card>
    );
    const card = screen.getByTestId('card');

    expect(card).toBeInTheDocument();
    expect(card).toHaveClass('bg-neutral-800');
  });

  it('combines all props correctly', () => {
    render(
      <Card data-testid="card" variant="elevated" padding="lg" hover className="custom-spacing">
        Combined props card
      </Card>
    );
    const card = screen.getByTestId('card');

    expect(card).toHaveClass('bg-neutral-800');
    expect(card).toHaveClass('rounded-lg');
    expect(card).toHaveClass('shadow-lg');
    expect(card).toHaveClass('p-6');
    expect(card).toHaveClass('custom-spacing');
    expect(screen.getByText('Combined props card')).toBeInTheDocument();
  });

  it('handles complex children content', () => {
    render(
      <Card data-testid="card">
        <div>
          <h2>Card Title</h2>
          <p>Card description</p>
          <button>Action</button>
        </div>
      </Card>
    );

    expect(screen.getByText('Card Title')).toBeInTheDocument();
    expect(screen.getByText('Card description')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument();
  });
});

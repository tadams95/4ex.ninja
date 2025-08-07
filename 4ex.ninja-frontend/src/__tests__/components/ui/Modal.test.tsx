import { Modal } from '@/components/ui/Modal';
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('Modal Component', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    mockOnClose.mockClear();
  });

  it('renders modal when isOpen is true', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose}>
        <p>Modal content</p>
      </Modal>
    );

    expect(screen.getByText('Modal content')).toBeInTheDocument();
  });

  it('does not render modal when isOpen is false', () => {
    render(
      <Modal isOpen={false} onClose={mockOnClose}>
        <p>Modal content</p>
      </Modal>
    );

    expect(screen.queryByText('Modal content')).not.toBeInTheDocument();
  });

  it('renders title when provided', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose} title="Test Modal">
        <p>Modal content</p>
      </Modal>
    );

    expect(screen.getByText('Test Modal')).toBeInTheDocument();
    expect(screen.getByLabelText('Close modal')).toBeInTheDocument();
  });

  it('applies correct size classes', () => {
    const { rerender } = render(
      <Modal isOpen={true} onClose={mockOnClose} size="sm">
        <p>Small modal</p>
      </Modal>
    );

    // Find the modal container (second div child, first is backdrop)
    let modalContainer = document.querySelector('.max-w-sm');
    expect(modalContainer).toBeInTheDocument();

    rerender(
      <Modal isOpen={true} onClose={mockOnClose} size="md">
        <p>Medium modal</p>
      </Modal>
    );
    modalContainer = document.querySelector('.max-w-md');
    expect(modalContainer).toBeInTheDocument();

    rerender(
      <Modal isOpen={true} onClose={mockOnClose} size="lg">
        <p>Large modal</p>
      </Modal>
    );
    modalContainer = document.querySelector('.max-w-lg');
    expect(modalContainer).toBeInTheDocument();

    rerender(
      <Modal isOpen={true} onClose={mockOnClose} size="xl">
        <p>Extra large modal</p>
      </Modal>
    );
    modalContainer = document.querySelector('.max-w-xl');
    expect(modalContainer).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose} className="custom-modal">
        <p>Custom modal</p>
      </Modal>
    );

    const modalContainer = document.querySelector('.custom-modal');
    expect(modalContainer).toBeInTheDocument();
  });

  it('calls onClose when backdrop is clicked', async () => {
    const user = userEvent.setup();

    render(
      <Modal isOpen={true} onClose={mockOnClose}>
        <p>Modal content</p>
      </Modal>
    );

    // Click on the backdrop (the overlay behind the modal)
    const backdrop = screen.getByText('Modal content').closest('.fixed')?.firstChild;
    if (backdrop) {
      await user.click(backdrop as Element);
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    }
  });

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup();

    render(
      <Modal isOpen={true} onClose={mockOnClose} title="Test Modal">
        <p>Modal content</p>
      </Modal>
    );

    const closeButton = screen.getByLabelText('Close modal');
    await user.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when Escape key is pressed', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose}>
        <p>Modal content</p>
      </Modal>
    );

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('does not call onClose for other keys', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose}>
        <p>Modal content</p>
      </Modal>
    );

    fireEvent.keyDown(document, { key: 'Enter' });
    fireEvent.keyDown(document, { key: 'Space' });

    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it('sets body overflow to hidden when modal is open', () => {
    const originalOverflow = document.body.style.overflow;

    render(
      <Modal isOpen={true} onClose={mockOnClose}>
        <p>Modal content</p>
      </Modal>
    );

    expect(document.body.style.overflow).toBe('hidden');

    // Cleanup - restore original overflow
    document.body.style.overflow = originalOverflow;
  });

  it('restores body overflow when modal is closed', () => {
    const { unmount } = render(
      <Modal isOpen={true} onClose={mockOnClose}>
        <p>Modal content</p>
      </Modal>
    );

    expect(document.body.style.overflow).toBe('hidden');

    unmount();

    expect(document.body.style.overflow).toBe('unset');
  });

  it('handles modal without title correctly', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose}>
        <p>Modal without title</p>
      </Modal>
    );

    expect(screen.getByText('Modal without title')).toBeInTheDocument();
    expect(screen.queryByLabelText('Close modal')).not.toBeInTheDocument();
  });

  it('renders complex children content', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose} title="Complex Modal">
        <div>
          <h3>Section Title</h3>
          <p>Some description text</p>
          <button>Action Button</button>
          <input placeholder="Enter value" />
        </div>
      </Modal>
    );

    expect(screen.getByText('Complex Modal')).toBeInTheDocument();
    expect(screen.getByText('Section Title')).toBeInTheDocument();
    expect(screen.getByText('Some description text')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Action Button' })).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter value')).toBeInTheDocument();
  });

  it('has proper accessibility attributes', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose} title="Accessible Modal">
        <p>Modal content</p>
      </Modal>
    );

    const closeButton = screen.getByLabelText('Close modal');
    expect(closeButton).toHaveAttribute('aria-label', 'Close modal');
  });
});

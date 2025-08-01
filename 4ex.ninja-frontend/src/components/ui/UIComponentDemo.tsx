/* 
UI Component Library Demo
This file demonstrates all the available UI components and their usage.
Remove this file after you've familiarized yourself with the component library.
*/

'use client';

import { Button, Card, Input, LoadingSpinner, Modal } from '@/components/ui';
import React, { useState } from 'react';

export const UIComponentDemo: React.FC = () => {
  const [modalOpen, setModalOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [inputError, setInputError] = useState('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
    if (e.target.value.length < 3) {
      setInputError('Must be at least 3 characters');
    } else {
      setInputError('');
    }
  };

  return (
    <div className="p-8 space-y-8 bg-black min-h-screen text-white">
      <h1 className="text-3xl font-bold text-center mb-8">4ex.ninja UI Component Library</h1>

      {/* Buttons */}
      <Card variant="elevated" padding="lg">
        <h2 className="text-xl font-semibold mb-4">Buttons</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-gray-300">Primary</h3>
            <Button variant="primary" size="sm">
              Small
            </Button>
            <Button variant="primary" size="md">
              Medium
            </Button>
            <Button variant="primary" size="lg">
              Large
            </Button>
          </div>
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-gray-300">Secondary</h3>
            <Button variant="secondary" size="sm">
              Small
            </Button>
            <Button variant="secondary" size="md">
              Medium
            </Button>
            <Button variant="secondary" size="lg">
              Large
            </Button>
          </div>
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-gray-300">Outline</h3>
            <Button variant="outline" size="sm">
              Small
            </Button>
            <Button variant="outline" size="md">
              Medium
            </Button>
            <Button variant="outline" size="lg">
              Large
            </Button>
          </div>
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-gray-300">States</h3>
            <Button variant="primary" loading>
              Loading
            </Button>
            <Button variant="primary" disabled>
              Disabled
            </Button>
            <Button variant="ghost">Ghost</Button>
          </div>
        </div>
      </Card>

      {/* Inputs */}
      <Card variant="elevated" padding="lg">
        <h2 className="text-xl font-semibold mb-4">Inputs</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Basic Input"
            placeholder="Enter some text..."
            value={inputValue}
            onChange={handleInputChange}
            error={inputError}
            helperText="This is helper text"
          />
          <Input label="Email Input" type="email" placeholder="your@email.com" variant="rounded" />
          <Input label="Password Input" type="password" placeholder="Enter password" />
          <Input placeholder="No label input" disabled value="Disabled input" />
        </div>
      </Card>

      {/* Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card variant="default" padding="lg">
          <h3 className="text-lg font-semibold mb-2">Default Card</h3>
          <p className="text-gray-300">This is a default card with standard styling.</p>
        </Card>
        <Card variant="elevated" padding="lg" hover>
          <h3 className="text-lg font-semibold mb-2">Elevated Card (Hover)</h3>
          <p className="text-gray-300">This card has elevation and hover effects.</p>
        </Card>
        <Card variant="outlined" padding="lg">
          <h3 className="text-lg font-semibold mb-2">Outlined Card</h3>
          <p className="text-gray-300">This card has a border outline.</p>
        </Card>
      </div>

      {/* Loading Spinners */}
      <Card variant="elevated" padding="lg">
        <h2 className="text-xl font-semibold mb-4">Loading Spinners</h2>
        <div className="flex items-center space-x-8">
          <div className="text-center">
            <LoadingSpinner size="sm" />
            <p className="text-sm mt-2">Small</p>
          </div>
          <div className="text-center">
            <LoadingSpinner size="md" />
            <p className="text-sm mt-2">Medium</p>
          </div>
          <div className="text-center">
            <LoadingSpinner size="lg" />
            <p className="text-sm mt-2">Large</p>
          </div>
          <div className="text-center">
            <LoadingSpinner size="xl" color="white" />
            <p className="text-sm mt-2">Extra Large</p>
          </div>
        </div>
      </Card>

      {/* Modal */}
      <Card variant="elevated" padding="lg">
        <h2 className="text-xl font-semibold mb-4">Modal</h2>
        <Button onClick={() => setModalOpen(true)}>Open Modal</Button>

        <Modal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title="Example Modal"
          size="md"
        >
          <div className="space-y-4">
            <p className="text-gray-300">
              This is an example modal with proper backdrop, animations, and keyboard support.
            </p>
            <Input label="Modal Input" placeholder="Type something..." />
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setModalOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" onClick={() => setModalOpen(false)}>
                Confirm
              </Button>
            </div>
          </div>
        </Modal>
      </Card>

      {/* Usage Instructions */}
      <Card variant="outlined" padding="lg">
        <h2 className="text-xl font-semibold mb-4">Usage Instructions</h2>
        <div className="text-gray-300 space-y-2">
          <p>
            <strong>Import:</strong>{' '}
            <code className="bg-gray-700 px-2 py-1 rounded">
              import {`{ Button, Input, Card }`} from '@/components/ui';
            </code>
          </p>
          <p>
            <strong>TypeScript:</strong> All components include full TypeScript support with proper
            type definitions.
          </p>
          <p>
            <strong>Styling:</strong> Components follow the existing 4ex.ninja design system with
            black/gray theme and green accents.
          </p>
          <p>
            <strong>Animation:</strong> Enhanced with Framer Motion for smooth interactions.
          </p>
          <p>
            <strong>Accessibility:</strong> Includes proper ARIA attributes and keyboard navigation
            support.
          </p>
        </div>
      </Card>
    </div>
  );
};

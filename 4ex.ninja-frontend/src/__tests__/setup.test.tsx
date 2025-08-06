/**
 * @jest-environment jsdom
 */

import { createTestCrossover, createTestUser } from '@/test-utils/database';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

describe('Testing Infrastructure Setup', () => {
  describe('Jest Configuration', () => {
    it('should be properly configured', () => {
      expect(jest).toBeDefined();
      expect(typeof jest.fn).toBe('function');
    });
  });

  describe('React Testing Library', () => {
    it('should render a simple component', () => {
      render(<div data-testid="test-element">Hello World</div>);
      expect(screen.getByTestId('test-element')).toBeInTheDocument();
      expect(screen.getByText('Hello World')).toBeInTheDocument();
    });
  });

  describe('Test Utilities', () => {
    it('should create test users', () => {
      const user = createTestUser();
      expect(user).toMatchObject({
        id: expect.any(String),
        name: expect.any(String),
        email: expect.any(String),
        isSubscribed: expect.any(Boolean),
        subscriptionStatus: expect.any(String),
      });
    });

    it('should create test crossovers', () => {
      const crossover = createTestCrossover();
      expect(crossover).toMatchObject({
        id: expect.any(String),
        pair: expect.any(String),
        signal: expect.any(String),
        confidence: expect.any(Number),
        entry_price: expect.any(Number),
      });
    });

    it('should allow overrides in test data', () => {
      const customUser = createTestUser({
        name: 'Custom User',
        isSubscribed: false,
      });
      expect(customUser.name).toBe('Custom User');
      expect(customUser.isSubscribed).toBe(false);
    });
  });

  describe('Environment Setup', () => {
    it('should have test environment', () => {
      // Basic environment test
      expect(typeof window).toBe('object');
      expect(typeof document).toBe('object');
    });
  });
});

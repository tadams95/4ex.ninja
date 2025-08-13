/**
 * @jest-environment jsdom
 */

import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';

// Test utility functions for inline use
const createTestUser = (overrides = {}) => ({
  id: 'test-user-123',
  name: 'Test User',
  email: 'test@example.com',
  isSubscribed: true,
  subscriptionStatus: 'active',
  subscriptionEnds: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
  ...overrides,
});

const createTestCrossover = (overrides = {}) => ({
  id: 'test-crossover-123',
  pair: 'EUR/USD',
  signal: 'BUY',
  confidence: 85,
  entry_price: 1.095,
  stop_loss: 1.09,
  take_profit: 1.1,
  created_at: new Date().toISOString(),
  strategy: 'MA_CROSSOVER',
  timeframe: 'H4',
  ...overrides,
});

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

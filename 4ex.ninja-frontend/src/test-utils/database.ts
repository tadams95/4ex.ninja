// Database test utilities
// Note: These are lightweight utilities that work with MSW mocks
// For full database integration tests, use the backend testing setup

export interface TestUser {
  id: string;
  name: string;
  email: string;
  isSubscribed: boolean;
  subscriptionStatus: string;
  subscriptionEnds: string;
}

export interface TestCrossover {
  id: string;
  pair: string;
  signal: string;
  confidence: number;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  created_at: string;
  strategy: string;
  timeframe: string;
}

// Test data factory functions
export const createTestUser = (overrides: Partial<TestUser> = {}): TestUser => ({
  id: `test-user-${Date.now()}`,
  name: 'Test User',
  email: 'test@example.com',
  isSubscribed: true,
  subscriptionStatus: 'active',
  subscriptionEnds: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
  ...overrides,
});

export const createTestCrossover = (overrides: Partial<TestCrossover> = {}): TestCrossover => ({
  id: `test-crossover-${Date.now()}`,
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

// Test data collections
export const createTestUserCollection = (count: number = 5): TestUser[] => {
  return Array.from({ length: count }, (_, index) =>
    createTestUser({
      id: `test-user-${index + 1}`,
      email: `test${index + 1}@example.com`,
      name: `Test User ${index + 1}`,
    })
  );
};

export const createTestCrossoverCollection = (count: number = 10): TestCrossover[] => {
  const pairs = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD'];
  const signals = ['BUY', 'SELL'];

  return Array.from({ length: count }, (_, index) =>
    createTestCrossover({
      id: `test-crossover-${index + 1}`,
      pair: pairs[index % pairs.length],
      signal: signals[index % signals.length],
      confidence: 60 + (index % 40), // Confidence between 60-99
      entry_price: 1.0 + index * 0.001, // Varying prices
      created_at: new Date(Date.now() - index * 60 * 60 * 1000).toISOString(), // Staggered times
    })
  );
};

// Utility functions for test data manipulation
export const filterCrossoversByPair = (
  crossovers: TestCrossover[],
  pair: string
): TestCrossover[] => {
  return crossovers.filter(c => c.pair === pair);
};

export const filterCrossoversBySignal = (
  crossovers: TestCrossover[],
  signal: string
): TestCrossover[] => {
  return crossovers.filter(c => c.signal === signal);
};

export const sortCrossoversByDate = (
  crossovers: TestCrossover[],
  direction: 'asc' | 'desc' = 'desc'
): TestCrossover[] => {
  return [...crossovers].sort((a, b) => {
    const dateA = new Date(a.created_at).getTime();
    const dateB = new Date(b.created_at).getTime();
    return direction === 'desc' ? dateB - dateA : dateA - dateB;
  });
};

// Mock API response helpers
export const createApiResponse = <T>(data: T, success: boolean = true) => ({
  success,
  data,
  timestamp: new Date().toISOString(),
});

export const createErrorResponse = (message: string, code: number = 500) => ({
  success: false,
  error: {
    message,
    code,
    timestamp: new Date().toISOString(),
  },
});

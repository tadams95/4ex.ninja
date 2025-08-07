// Test data fixtures for LEAN E2E testing
// These represent the minimal data needed for 3 critical user journeys

export const testUsers = {
  validUser: {
    email: 'test.user@4ex.ninja',
    password: 'TestPass123!',
    firstName: 'Test',
    lastName: 'User',
  },
  premiumUser: {
    email: 'premium.user@4ex.ninja',
    password: 'PremiumPass123!',
    firstName: 'Premium',
    lastName: 'User',
    subscriptionTier: 'premium',
  },
  invalidUser: {
    email: 'invalid@4ex.ninja',
    password: 'wrongpass',
  },
};

export const tradingData = {
  validTrade: {
    pair: 'EUR/USD',
    amount: '1000',
    direction: 'buy',
    stopLoss: '1.0500',
    takeProfit: '1.1000',
  },
  invalidTrade: {
    pair: 'INVALID/PAIR',
    amount: '-100',
    direction: 'sell',
  },
};

export const subscriptionData = {
  basicPlan: {
    name: 'Basic Plan',
    price: '$29/month',
    features: ['Real-time data', 'Basic strategies'],
  },
  premiumPlan: {
    name: 'Premium Plan',
    price: '$99/month',
    features: ['Real-time data', 'Advanced strategies', 'API access'],
  },
  testCard: {
    number: '4242424242424242',
    expiry: '12/25',
    cvc: '123',
    name: 'Test User',
  },
};

export const apiEndpoints = {
  auth: {
    login: '/api/auth/login',
    register: '/api/auth/register',
    logout: '/api/auth/logout',
  },
  trading: {
    positions: '/api/trading/positions',
    orders: '/api/trading/orders',
    history: '/api/trading/history',
  },
  subscription: {
    plans: '/api/subscription/plans',
    subscribe: '/api/subscription/subscribe',
    cancel: '/api/subscription/cancel',
  },
};

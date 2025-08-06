import { http, HttpResponse } from 'msw';

// Mock data
const mockUser = {
  id: 'test-user-123',
  name: 'Test User',
  email: 'test@example.com',
  isSubscribed: true,
  subscriptionStatus: 'active',
  subscriptionEnds: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days from now
};

const mockCrossovers = [
  {
    id: '1',
    pair: 'EUR/USD',
    signal: 'BUY',
    confidence: 85,
    entry_price: 1.095,
    stop_loss: 1.09,
    take_profit: 1.1,
    created_at: new Date().toISOString(),
    strategy: 'MA_CROSSOVER',
    timeframe: 'H4',
  },
  {
    id: '2',
    pair: 'GBP/USD',
    signal: 'SELL',
    confidence: 72,
    entry_price: 1.265,
    stop_loss: 1.27,
    take_profit: 1.26,
    created_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(), // 1 hour ago
    strategy: 'MA_CROSSOVER',
    timeframe: 'H4',
  },
];

export const handlers = [
  // Authentication endpoints
  http.get('/api/auth/session', () => {
    return HttpResponse.json({
      user: mockUser,
      expires: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    });
  }),

  http.post('/api/auth/signin', () => {
    return HttpResponse.json({ success: true, user: mockUser });
  }),

  http.post('/api/auth/signout', () => {
    return HttpResponse.json({ success: true });
  }),

  // Subscription endpoints
  http.get('/api/subscription-status', () => {
    return HttpResponse.json({
      isSubscribed: mockUser.isSubscribed,
      subscriptionStatus: mockUser.subscriptionStatus,
      subscriptionEnds: mockUser.subscriptionEnds,
    });
  }),

  http.post('/api/verify-subscription', () => {
    return HttpResponse.json({
      valid: true,
      subscriptionStatus: 'active',
    });
  }),

  http.post('/api/create-checkout-session', () => {
    return HttpResponse.json({
      url: 'https://checkout.stripe.com/test-session',
      sessionId: 'cs_test_123456789',
    });
  }),

  http.post('/api/cancel-subscription', () => {
    return HttpResponse.json({
      success: true,
      message: 'Subscription cancelled successfully',
    });
  }),

  // User profile endpoints
  http.get('/api/user-profile', () => {
    return HttpResponse.json(mockUser);
  }),

  http.put('/api/update-profile', async ({ request }) => {
    const body = (await request.json()) as Partial<typeof mockUser>;
    return HttpResponse.json({
      ...mockUser,
      ...body,
    });
  }),

  // Crossovers/signals endpoints
  http.get('/api/crossovers', ({ request }) => {
    const url = new URL(request.url);
    const limit = url.searchParams.get('limit');
    const pair = url.searchParams.get('pair');

    let filteredCrossovers = mockCrossovers;

    if (pair) {
      filteredCrossovers = mockCrossovers.filter(c => c.pair === pair);
    }

    if (limit) {
      filteredCrossovers = filteredCrossovers.slice(0, parseInt(limit));
    }

    return HttpResponse.json({
      crossovers: filteredCrossovers,
      total: filteredCrossovers.length,
    });
  }),

  http.get('/api/signals', () => {
    return HttpResponse.json({
      signals: mockCrossovers,
      total: mockCrossovers.length,
    });
  }),

  // Debug endpoints
  http.get('/api/debug', () => {
    return HttpResponse.json({
      environment: 'test',
      timestamp: new Date().toISOString(),
    });
  }),

  // Error scenarios for testing
  http.get('/api/error/500', () => {
    return new HttpResponse(null, { status: 500 });
  }),

  http.get('/api/error/401', () => {
    return new HttpResponse(null, { status: 401 });
  }),

  http.get('/api/error/403', () => {
    return new HttpResponse(null, { status: 403 });
  }),

  // Webhook endpoint (for testing)
  http.post('/api/webhook', () => {
    return HttpResponse.json({ received: true });
  }),
];

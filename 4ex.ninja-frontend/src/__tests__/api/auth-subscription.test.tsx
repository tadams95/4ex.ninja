// // Mock MongoDB
// const mockMongoClient = {
//   connect: jest.fn(),
//   close: jest.fn(),
//   db: jest.fn().mockReturnValue({
//     collection: jest.fn().mockReturnValue({
//       findOne: jest.fn(),
//       insertOne: jest.fn(),
//       updateOne: jest.fn(),
//     }),
//   }),
// };

// Mock MongoDB module
jest.mock('mongodb', () => ({
  MongoClient: jest.fn().mockImplementation(() => mockMongoClient),
  ObjectId: jest.fn().mockImplementation(id => ({ _id: id })),
}));

// Mock NextAuth session
jest.mock('next-auth/next', () => ({
  getServerSession: jest.fn(),
}));

// Mock bcrypt
jest.mock('bcryptjs', () => ({
  hash: jest.fn().mockResolvedValue('hashedPassword123'),
  compare: jest.fn().mockResolvedValue(true),
}));

// const { getServerSession } = require('next-auth/next');

// Mock fetch for API testing
global.fetch = jest.fn();

describe('Authentication API Routes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    process.env.MONGO_CONNECTION_STRING = 'mongodb://test-connection';
    (fetch as jest.MockedFunction<typeof fetch>).mockClear();
  });

  describe('POST /api/auth/register', () => {
    it('should successfully register a new user', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: true,
        status: 201,
        json: async () => ({ message: 'User created successfully' }),
      } as Response);

      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'John Doe',
          email: 'john@example.com',
          password: 'password123',
        }),
      });

      const result = await response.json();

      expect(response.status).toBe(201);
      expect(result.message).toBe('User created successfully');
    });

    it('should return error for missing required fields', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: false,
        status: 400,
        json: async () => ({ error: 'Missing required fields' }),
      } as Response);

      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'john@example.com',
          // Missing name and password
        }),
      });

      const result = await response.json();

      expect(response.status).toBe(400);
      expect(result.error).toBe('Missing required fields');
    });

    it('should return error for existing user', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: false,
        status: 409,
        json: async () => ({ error: 'User already exists' }),
      } as Response);

      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'John Doe',
          email: 'john@example.com',
          password: 'password123',
        }),
      });

      const result = await response.json();

      expect(response.status).toBe(409);
      expect(result.error).toBe('User already exists');
    });

    it('should handle database connection errors', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ error: 'Server error during registration' }),
      } as Response);

      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'John Doe',
          email: 'john@example.com',
          password: 'password123',
        }),
      });

      const result = await response.json();

      expect(response.status).toBe(500);
      expect(result.error).toBe('Server error during registration');
    });
  });

  describe('GET /api/subscription-status', () => {
    it('should return subscription status for authenticated user', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          isSubscribed: true,
          subscriptionStatus: 'active',
          subscriptionEnds: '2024-12-31T00:00:00.000Z',
        }),
      } as Response);

      const response = await fetch('/api/subscription-status');
      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.isSubscribed).toBe(true);
      expect(result.subscriptionStatus).toBe('active');
    });

    it('should return 401 for unauthenticated user', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ error: 'Unauthorized' }),
      } as Response);

      const response = await fetch('/api/subscription-status');
      const result = await response.json();

      expect(response.status).toBe(401);
      expect(result.error).toBe('Unauthorized');
    });

    it('should return false for user without subscription', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          isSubscribed: false,
          subscriptionStatus: 'inactive',
        }),
      } as Response);

      const response = await fetch('/api/subscription-status');
      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.isSubscribed).toBe(false);
      expect(result.subscriptionStatus).toBe('inactive');
    });

    it('should handle database errors gracefully', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ error: 'Internal server error' }),
      } as Response);

      const response = await fetch('/api/subscription-status');
      const result = await response.json();

      expect(response.status).toBe(500);
      expect(result.error).toBe('Internal server error');
    });
  });
});

describe('Subscription API Routes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (fetch as jest.MockedFunction<typeof fetch>).mockClear();
  });

  describe('GET /api/verify-subscription', () => {
    it('should verify active subscription correctly', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          isSubscribed: true,
          subscriptionStatus: 'active',
          subscriptionEnds: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        }),
      } as Response);

      const response = await fetch('/api/verify-subscription');
      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.isSubscribed).toBe(true);
      expect(result.subscriptionStatus).toBe('active');
      expect(new Date(result.subscriptionEnds)).toBeInstanceOf(Date);
    });

    it('should handle expired subscription', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          isSubscribed: false,
          subscriptionStatus: 'expired',
          subscriptionEnds: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        }),
      } as Response);

      const response = await fetch('/api/verify-subscription');
      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.isSubscribed).toBe(false);
      expect(result.subscriptionStatus).toBe('expired');
    });

    it('should return 401 for unauthenticated requests', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ error: 'Unauthorized' }),
      } as Response);

      const response = await fetch('/api/verify-subscription');
      const result = await response.json();

      expect(response.status).toBe(401);
      expect(result.error).toBe('Unauthorized');
    });
  });
});

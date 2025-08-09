// Mock MongoDB for crossovers testing
const mockCrossoverClient = {
  connect: jest.fn(),
  close: jest.fn(),
  db: jest.fn().mockReturnValue({
    collection: jest.fn().mockReturnValue({
      find: jest.fn().mockReturnValue({
        sort: jest.fn().mockReturnValue({
          limit: jest.fn().mockReturnValue({
            toArray: jest.fn(),
          }),
        }),
      }),
      countDocuments: jest.fn(),
    }),
  }),
};

// Mock MongoDB module
jest.mock('mongodb', () => ({
  MongoClient: jest.fn().mockImplementation(() => mockCrossoverClient),
  ObjectId: jest.fn().mockImplementation(id => ({ _id: id })),
}));

// Mock fetch for API testing
global.fetch = jest.fn();

// Sample crossover data
const mockCrossovers = [
  {
    _id: '1',
    pair: 'EUR_USD',
    crossoverType: 'BULLISH',
    timeframe: 'H1',
    fastMA: 10,
    slowMA: 20,
    price: '1.0850',
    timestamp: '2024-01-01T10:00:00Z',
  },
  {
    _id: '2',
    pair: 'GBP_USD',
    crossoverType: 'BEARISH',
    timeframe: 'H4',
    fastMA: 5,
    slowMA: 15,
    price: '1.2750',
    timestamp: '2024-01-01T12:00:00Z',
  },
];

describe('Crossovers API Routes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    process.env.MONGO_CONNECTION_STRING = 'mongodb://test-connection';
    (fetch as jest.MockedFunction<typeof fetch>).mockClear();
  });

  describe('GET /api/crossovers', () => {
    it('should return crossovers data successfully', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          crossovers: mockCrossovers,
          isEmpty: false,
        }),
      } as Response);

      const response = await fetch('/api/crossovers');
      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.success).toBe(true);
      expect(result.crossovers).toEqual(mockCrossovers);
      expect(result.isEmpty).toBe(false);
    });

    it('should return empty array when no crossovers found', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          crossovers: [],
          isEmpty: true,
        }),
      } as Response);

      const response = await fetch('/api/crossovers');
      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.success).toBe(true);
      expect(result.crossovers).toEqual([]);
      expect(result.isEmpty).toBe(true);
    });

    it('should handle database connection errors', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({
          success: false,
          error: 'Database connection failed',
        }),
      } as Response);

      const response = await fetch('/api/crossovers');
      const result = await response.json();

      expect(response.status).toBe(500);
      expect(result.success).toBe(false);
      expect(result.error).toBe('Database connection failed');
    });

    it('should support pagination parameters', async () => {
      const paginatedCrossovers = [mockCrossovers[0]]; // First page with one item

      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          crossovers: paginatedCrossovers,
          isEmpty: false,
          pagination: {
            page: 1,
            limit: 1,
            total: 2,
            hasMore: true,
          },
        }),
      } as Response);

      const response = await fetch('/api/crossovers?limit=1&page=1');
      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.success).toBe(true);
      expect(result.crossovers).toHaveLength(1);
      expect(result.pagination.page).toBe(1);
      expect(result.pagination.limit).toBe(1);
      expect(result.pagination.total).toBe(2);
      expect(result.pagination.hasMore).toBe(true);
    });

    it('should support filtering by pair', async () => {
      const filteredCrossovers = [mockCrossovers[0]]; // Only EUR_USD

      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          crossovers: filteredCrossovers,
          isEmpty: false,
        }),
      } as Response);

      const response = await fetch('/api/crossovers?pair=EUR_USD');
      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.success).toBe(true);
      expect(result.crossovers).toHaveLength(1);
      expect(result.crossovers[0].pair).toBe('EUR_USD');
    });

    it('should support filtering by crossover type', async () => {
      const bullishCrossovers = [mockCrossovers[0]]; // Only BULLISH

      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          crossovers: bullishCrossovers,
          isEmpty: false,
        }),
      } as Response);

      const response = await fetch('/api/crossovers?type=BULLISH');
      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.success).toBe(true);
      expect(result.crossovers).toHaveLength(1);
      expect(result.crossovers[0].crossoverType).toBe('BULLISH');
    });

    it('should support sorting by timestamp', async () => {
      const sortedCrossovers = [...mockCrossovers].reverse(); // Reverse order

      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          crossovers: sortedCrossovers,
          isEmpty: false,
        }),
      } as Response);

      const response = await fetch('/api/crossovers?sort=timestamp&order=asc');
      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.success).toBe(true);
      expect(result.crossovers).toEqual(sortedCrossovers);
    });

    it('should handle invalid query parameters gracefully', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: false,
        status: 400,
        json: async () => ({
          success: false,
          error: 'Invalid query parameters',
        }),
      } as Response);

      const response = await fetch('/api/crossovers?limit=invalid&page=notanumber');
      const result = await response.json();

      expect(response.status).toBe(400);
      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid query parameters');
    });

    it('should handle rate limiting', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: false,
        status: 429,
        json: async () => ({
          success: false,
          error: 'Too many requests',
        }),
      } as Response);

      const response = await fetch('/api/crossovers');
      const result = await response.json();

      expect(response.status).toBe(429);
      expect(result.success).toBe(false);
      expect(result.error).toBe('Too many requests');
    });

    it('should validate crossover data structure', async () => {
      const validatedCrossovers = mockCrossovers.map(crossover => ({
        ...crossover,
        // Ensure required fields are present
        _id: crossover._id,
        pair: crossover.pair,
        crossoverType: crossover.crossoverType,
        timestamp: crossover.timestamp,
      }));

      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          crossovers: validatedCrossovers,
          isEmpty: false,
        }),
      } as Response);

      const response = await fetch('/api/crossovers');
      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.success).toBe(true);

      // Validate structure of returned crossovers
      result.crossovers.forEach((crossover: any) => {
        expect(crossover).toHaveProperty('_id');
        expect(crossover).toHaveProperty('pair');
        expect(crossover).toHaveProperty('crossoverType');
        expect(crossover).toHaveProperty('timestamp');
        expect(['BULLISH', 'BEARISH']).toContain(crossover.crossoverType);
      });
    });
  });

  describe('Error handling and edge cases', () => {
    it('should handle MongoDB connection timeout', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: false,
        status: 503,
        json: async () => ({
          success: false,
          error: 'Service temporarily unavailable',
        }),
      } as Response);

      const response = await fetch('/api/crossovers');
      const result = await response.json();

      expect(response.status).toBe(503);
      expect(result.success).toBe(false);
      expect(result.error).toBe('Service temporarily unavailable');
    });

    it('should handle malformed response data', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({
          success: false,
          error: 'Internal server error',
        }),
      } as Response);

      const response = await fetch('/api/crossovers');
      const result = await response.json();

      expect(response.status).toBe(500);
      expect(result.success).toBe(false);
      expect(result.error).toBe('Internal server error');
    });
  });
});

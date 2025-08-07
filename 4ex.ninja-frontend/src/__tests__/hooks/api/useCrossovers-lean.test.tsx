import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import React, { ReactNode } from 'react';
import {
  crossoverKeys,
  useCrossovers,
  useLatestCrossovers,
} from '../../../hooks/api/useCrossovers';
import { Crossover } from '../../../types';

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock crossover data
const mockCrossovers: Crossover[] = [
  {
    _id: '1',
    pair: 'EUR/USD',
    crossoverType: 'BULLISH',
    timeframe: 'H4',
    fastMA: 20,
    slowMA: 50,
    price: '1.0850',
    timestamp: new Date('2024-01-01T10:00:00Z'),
    signal: 'Buy',
    close: 1.085,
    time: new Date('2024-01-01T10:00:00Z'),
  },
];

const mockSuccessResponse = {
  success: true,
  crossovers: mockCrossovers,
  isEmpty: false,
  total: 1,
};

// Test wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: Infinity,
      },
    },
  });

  const TestWrapper = ({ children }: { children: ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);

  return TestWrapper;
};

describe('useCrossovers Hook Tests', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic data fetching', () => {
    it('should fetch crossovers successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSuccessResponse),
      });

      const { result } = renderHook(() => useCrossovers(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toBeDefined();
      expect(result.current.data?.crossovers).toHaveLength(1);
      expect(result.current.error).toBeNull();
      expect(mockFetch).toHaveBeenCalledWith('/api/crossovers');
    });

    it('should handle API errors', async () => {
      const errorMessage = 'Failed to fetch crossovers';
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ error: errorMessage, success: false }),
      });

      const { result } = renderHook(() => useCrossovers(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      expect(result.current.error?.message).toBe(errorMessage);
      expect(result.current.data).toBeUndefined();
    });
  });

  describe('Filtering functionality', () => {
    it('should apply basic filters in API call', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSuccessResponse),
      });

      const filters = {
        pairs: ['EUR/USD'],
        timeframes: ['H4'],
        limit: 10,
      };

      renderHook(() => useCrossovers(filters), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/api/crossovers?'));
      });

      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain('pairs=EUR%2FUSD');
      expect(callUrl).toContain('timeframes=H4');
      expect(callUrl).toContain('limit=10');
    });

    it('should handle date filters', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSuccessResponse),
      });

      const filters = {
        startDate: '2024-01-01',
        endDate: '2024-01-31',
      };

      renderHook(() => useCrossovers(filters), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled();
      });

      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain('startDate=2024-01-01');
      expect(callUrl).toContain('endDate=2024-01-31');
    });
  });

  describe('Caching behavior', () => {
    it('should use correct query keys', () => {
      const filters = { pairs: ['EUR/USD'] };
      const expectedKey = crossoverKeys.list(filters);

      expect(expectedKey).toEqual(['crossovers', 'list', filters]);
    });

    it('should cache successful responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSuccessResponse),
      });

      const wrapper = createWrapper();
      const { result: result1 } = renderHook(() => useCrossovers(), { wrapper });

      await waitFor(() => {
        expect(result1.current.isLoading).toBe(false);
      });

      // Second render should use cached data
      const { result: result2 } = renderHook(() => useCrossovers(), { wrapper });

      expect(result2.current.isLoading).toBe(false);
      expect(result2.current.data).toEqual(result1.current.data);
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('Error handling', () => {
    it('should not retry on authorization errors', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ error: 'unauthorized', success: false }),
      });

      const { result } = renderHook(() => useCrossovers(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(result.current.error?.message).toBe('unauthorized');
    });
  });
});

describe('useLatestCrossovers Hook Tests', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should fetch latest crossovers with correct limit', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockSuccessResponse),
    });

    renderHook(() => useLatestCrossovers(15), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    const callUrl = mockFetch.mock.calls[0][0] as string;
    expect(callUrl).toContain('limit=15');
  });

  it('should use default limit when not specified', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockSuccessResponse),
    });

    renderHook(() => useLatestCrossovers(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    const callUrl = mockFetch.mock.calls[0][0] as string;
    expect(callUrl).toContain('limit=20');
  });
});

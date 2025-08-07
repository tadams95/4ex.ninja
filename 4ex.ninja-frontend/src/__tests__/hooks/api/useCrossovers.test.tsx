import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import React, { ReactNode } from 'react';
import {
  crossoverKeys,
  useCrossoverActions,
  useCrossovers,
  useFilteredCrossovers,
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
  {
    _id: '2',
    pair: 'GBP/USD',
    crossoverType: 'BEARISH',
    timeframe: 'H1',
    fastMA: 10,
    slowMA: 20,
    price: '1.2500',
    timestamp: new Date('2024-01-01T11:00:00Z'),
    signal: 'Sell',
    close: 1.25,
    time: new Date('2024-01-01T11:00:00Z'),
  },
];

const mockSuccessResponse = {
  success: true,
  crossovers: mockCrossovers,
  isEmpty: false,
  total: 2,
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

describe('useCrossovers', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic functionality', () => {
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

      expect(result.current.data).toEqual({
        ...mockSuccessResponse,
        crossovers: expect.arrayContaining([
          expect.objectContaining({
            ...mockCrossovers[0],
            timestamp: expect.any(Date),
            time: expect.any(Date),
          }),
        ]),
      });
      expect(result.current.error).toBeNull();
      expect(mockFetch).toHaveBeenCalledWith('/api/crossovers');
    });

    it('should handle API errors correctly', async () => {
      const errorMessage = 'Failed to fetch crossovers';
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ error: errorMessage, success: false }),
      });

      const { result } = renderHook(() => useCrossovers(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.error).toBeTruthy();
      expect(result.current.error?.message).toBe(errorMessage);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => useCrossovers(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.error).toBeTruthy();
      expect(result.current.error?.message).toBe('Network error');
    });
  });

  describe('Filtering functionality', () => {
    it('should apply filters correctly in API call', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSuccessResponse),
      });

      const filters = {
        pairs: ['EUR/USD', 'GBP/USD'],
        timeframes: ['H4'],
        signalTypes: ['BULLISH' as const],
        limit: 10,
        offset: 0,
      };

      renderHook(() => useCrossovers(filters), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          '/api/crossovers?pairs=EUR%2FUSD%2CGBP%2FUSD&timeframes=H4&signalTypes=BULLISH&limit=10&offset=0'
        );
      });
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
        expect(mockFetch).toHaveBeenCalledWith(
          '/api/crossovers?startDate=2024-01-01&endDate=2024-01-31'
        );
      });
    });
  });

  describe('Caching and invalidation', () => {
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

  describe('Real-time updates and polling', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.runOnlyPendingTimers();
      jest.useRealTimers();
    });

    it('should enable polling by default', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockSuccessResponse),
      });

      renderHook(() => useCrossovers(), {
        wrapper: createWrapper(),
      });

      // Initial call
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(1);
      });

      // Advance timer to trigger polling
      jest.advanceTimersByTime(5 * 60 * 1000); // 5 minutes

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2);
      });
    });

    it('should disable polling when requested', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockSuccessResponse),
      });

      renderHook(() => useCrossovers(undefined, { enablePolling: false }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(1);
      });

      // Advance timer - should not trigger additional calls
      jest.advanceTimersByTime(5 * 60 * 1000);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Error handling and retry logic', () => {
    it('should not retry on authorization errors', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ error: 'unauthorized', success: false }),
      });

      const { result } = renderHook(() => useCrossovers(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(result.current.error?.message).toBe('unauthorized');
    });

    it('should retry on server errors with limit', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          json: () => Promise.resolve({ error: '500 Internal Server Error', success: false }),
        })
        .mockResolvedValueOnce({
          ok: false,
          json: () => Promise.resolve({ error: '500 Internal Server Error', success: false }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockSuccessResponse),
        });

      const { result } = renderHook(() => useCrossovers(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Should have retried up to 2 times for server errors
      expect(mockFetch).toHaveBeenCalledTimes(3);
      expect(result.current.data).toEqual(expect.objectContaining(mockSuccessResponse));
    });
  });
});

describe('useLatestCrossovers', () => {
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
      expect(mockFetch).toHaveBeenCalledWith('/api/crossovers?limit=15&offset=0');
    });
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
      expect(mockFetch).toHaveBeenCalledWith('/api/crossovers?limit=20&offset=0');
    });
  });
});

describe('useFilteredCrossovers', () => {
  it('should disable polling for filtered views', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockSuccessResponse),
    });

    const filters = { pairs: ['EUR/USD'] };

    renderHook(() => useFilteredCrossovers(filters), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    // Should not poll for filtered views
    jest.useFakeTimers();
    jest.advanceTimersByTime(5 * 60 * 1000);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    jest.useRealTimers();
  });
});

describe('useCrossoverActions', () => {
  it('should provide cache management functions', () => {
    const { result } = renderHook(() => useCrossoverActions(), {
      wrapper: createWrapper(),
    });

    expect(result.current.invalidateAll).toBeInstanceOf(Function);
    expect(result.current.invalidateList).toBeInstanceOf(Function);
    expect(result.current.addCrossover).toBeInstanceOf(Function);
    expect(result.current.removeCrossover).toBeInstanceOf(Function);
  });

  it('should add crossover to cache correctly', async () => {
    // First populate the cache
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockSuccessResponse),
    });

    const wrapper = createWrapper();
    const { result: crossoverResult } = renderHook(() => useCrossovers(), { wrapper });
    const { result: actionsResult } = renderHook(() => useCrossoverActions(), { wrapper });

    await waitFor(() => {
      expect(crossoverResult.current.isLoading).toBe(false);
    });

    // Add new crossover
    const newCrossover: Crossover = {
      _id: '3',
      pair: 'USD/JPY',
      crossoverType: 'BULLISH',
      timeframe: 'D1',
      fastMA: 50,
      slowMA: 200,
      price: '110.50',
      timestamp: new Date('2024-01-01T12:00:00Z'),
      signal: 'Buy',
      close: 110.5,
    };

    actionsResult.current.addCrossover(newCrossover);

    // Check that new crossover was added to the beginning
    expect(crossoverResult.current.data?.crossovers[0]).toEqual(newCrossover);
    expect(crossoverResult.current.data?.crossovers).toHaveLength(3);
  });
});

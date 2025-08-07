import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { crossoverKeys, useCrossovers } from '../../../hooks/api/useCrossovers';

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock data
const mockCrossovers = [
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

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: 0 },
    },
  });

  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
};

describe('useCrossovers - Core Functionality', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should initialize and make API call', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          success: true,
          crossovers: mockCrossovers,
        }),
    });

    const { result } = renderHook(() => useCrossovers(), {
      wrapper: createWrapper(),
    });

    // Initial state
    expect(result.current.isLoading).toBe(true);

    // Wait for completion
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Verify API was called
    expect(mockFetch).toHaveBeenCalledWith('/api/crossovers');
  });

  it('should generate correct query keys', () => {
    const filters = { pairs: ['EUR/USD'] };
    const key = crossoverKeys.list(filters);
    expect(key).toEqual(['crossovers', 'list', filters]);
  });

  it('should apply URL parameters for filters', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: true, crossovers: [] }),
    });

    renderHook(() => useCrossovers({ pairs: ['EUR/USD'], limit: 5 }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    const calledUrl = mockFetch.mock.calls[0][0];
    expect(calledUrl).toContain('pairs=');
    expect(calledUrl).toContain('limit=5');
  });
});

describe('Query Key Generation', () => {
  it('should create base query key', () => {
    expect(crossoverKeys.all).toEqual(['crossovers']);
  });

  it('should create list query key with filters', () => {
    const filters = { timeframes: ['H4'] };
    expect(crossoverKeys.list(filters)).toEqual(['crossovers', 'list', filters]);
  });

  it('should create list query key without filters', () => {
    expect(crossoverKeys.list()).toEqual(['crossovers', 'list', undefined]);
  });
});

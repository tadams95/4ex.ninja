import { act, renderHook } from '@testing-library/react';
import { useCrossoverStore } from '../../stores/crossoverStore';

// Mock crossover data matching the actual Crossover interface
const mockCrossovers = [
  {
    _id: '1',
    pair: 'EUR_USD',
    crossoverType: 'BULLISH' as const,
    timeframe: 'H1',
    fastMA: 10,
    slowMA: 20,
    price: '1.0850',
    timestamp: '2024-01-01T10:00:00Z',
  },
  {
    _id: '2',
    pair: 'GBP_USD',
    crossoverType: 'BEARISH' as const,
    timeframe: 'H4',
    fastMA: 5,
    slowMA: 15,
    price: '1.2750',
    timestamp: '2024-01-01T12:00:00Z',
  },
];

describe('crossoverStore - Core Functionality', () => {
  beforeEach(() => {
    // Reset store before each test
    useCrossoverStore.getState().reset();
  });

  describe('Crossover data management', () => {
    it('should initialize with default state', () => {
      const { result } = renderHook(() => useCrossoverStore());

      expect(result.current.crossovers).toEqual([]);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.isEmpty).toBe(false);
    });

    it('should set crossovers data', () => {
      const { result } = renderHook(() => useCrossoverStore());

      act(() => {
        result.current.setCrossovers(mockCrossovers);
      });

      expect(result.current.crossovers).toEqual(mockCrossovers);
    });

    it('should add individual crossover', () => {
      const { result } = renderHook(() => useCrossoverStore());

      act(() => {
        result.current.addCrossover(mockCrossovers[0]);
      });

      expect(result.current.crossovers).toHaveLength(1);
      expect(result.current.crossovers[0]).toEqual(mockCrossovers[0]);
    });

    it('should handle loading and error states', () => {
      const { result } = renderHook(() => useCrossoverStore());

      act(() => {
        result.current.setLoading(true);
      });

      expect(result.current.loading).toBe(true);

      act(() => {
        result.current.setError('Failed to load data');
      });

      expect(result.current.error).toBe('Failed to load data');
    });

    it('should remove crossover', () => {
      const { result } = renderHook(() => useCrossoverStore());

      act(() => {
        result.current.setCrossovers(mockCrossovers);
      });

      act(() => {
        result.current.removeCrossover('1');
      });

      expect(result.current.crossovers).toHaveLength(1);
      expect(result.current.crossovers[0]._id).toBe('2');
    });
  });

  describe('Filtering functionality', () => {
    it('should toggle pair filter', () => {
      const { result } = renderHook(() => useCrossoverStore());

      act(() => {
        result.current.togglePairFilter('EUR_USD');
      });

      expect(result.current.filters.pairs).toContain('EUR_USD');

      act(() => {
        result.current.togglePairFilter('EUR_USD');
      });

      expect(result.current.filters.pairs).not.toContain('EUR_USD');
    });

    it('should toggle timeframe filter', () => {
      const { result } = renderHook(() => useCrossoverStore());

      act(() => {
        result.current.toggleTimeframeFilter('H4');
      });

      expect(result.current.filters.timeframes).toContain('H4');
    });

    it('should toggle signal type filter', () => {
      const { result } = renderHook(() => useCrossoverStore());

      act(() => {
        result.current.toggleSignalTypeFilter('BULLISH');
      });

      expect(result.current.filters.signalTypes).toContain('BULLISH');
    });

    it('should reset all filters', () => {
      const { result } = renderHook(() => useCrossoverStore());

      act(() => {
        result.current.togglePairFilter('EUR_USD');
        result.current.toggleTimeframeFilter('H4');
        result.current.toggleSignalTypeFilter('BULLISH');
      });

      act(() => {
        result.current.resetFilters();
      });

      expect(result.current.filters.pairs).toHaveLength(0);
      expect(result.current.filters.timeframes).toHaveLength(0);
      expect(result.current.filters.signalTypes).toHaveLength(0);
    });
  });

  describe('Sorting functionality', () => {
    it('should set sorting configuration', () => {
      const { result } = renderHook(() => useCrossoverStore());

      act(() => {
        result.current.setSorting({ field: 'timestamp', direction: 'asc' });
      });

      expect(result.current.sorting.field).toBe('timestamp');
      expect(result.current.sorting.direction).toBe('asc');
    });

    it('should toggle sort direction', () => {
      const { result } = renderHook(() => useCrossoverStore());

      const initialDirection = result.current.sorting.direction;

      act(() => {
        result.current.toggleSortDirection();
      });

      expect(result.current.sorting.direction).toBe(initialDirection === 'asc' ? 'desc' : 'asc');
    });
  });

  describe('Pagination functionality', () => {
    it('should set current page', () => {
      const { result } = renderHook(() => useCrossoverStore());

      act(() => {
        result.current.setCurrentPage(2);
      });

      expect(result.current.currentPage).toBe(2);
    });

    it('should set items per page', () => {
      const { result } = renderHook(() => useCrossoverStore());

      act(() => {
        result.current.setItemsPerPage(50);
      });

      expect(result.current.itemsPerPage).toBe(50);
    });
  });

  describe('Search functionality', () => {
    it('should set search query', () => {
      const { result } = renderHook(() => useCrossoverStore());

      act(() => {
        result.current.setSearchQuery('EUR');
      });

      expect(result.current.searchQuery).toBe('EUR');
    });
  });

  describe('Store utilities', () => {
    it('should reset to initial state', () => {
      const { result } = renderHook(() => useCrossoverStore());

      act(() => {
        result.current.setCrossovers(mockCrossovers);
        result.current.togglePairFilter('EUR_USD');
        result.current.setCurrentPage(3);
        result.current.setError('Some error');
      });

      act(() => {
        result.current.reset();
      });

      expect(result.current.crossovers).toEqual([]);
      expect(result.current.filters.pairs).toHaveLength(0);
      expect(result.current.currentPage).toBe(1);
      expect(result.current.error).toBeNull();
    });
  });
});

describe('crossoverStore - Selectors', () => {
  beforeEach(() => {
    useCrossoverStore.getState().reset();
  });

  it('should provide crossovers selector', () => {
    const { result } = renderHook(() => useCrossoverStore(state => state.crossovers));

    expect(result.current).toEqual([]);

    act(() => {
      useCrossoverStore.getState().setCrossovers(mockCrossovers);
    });

    expect(result.current).toEqual(mockCrossovers);
  });

  it('should provide filters selector', () => {
    const { result } = renderHook(() => useCrossoverStore(state => state.filters));

    expect(result.current.pairs).toHaveLength(0);

    act(() => {
      useCrossoverStore.getState().togglePairFilter('EUR_USD');
    });

    expect(result.current.pairs).toContain('EUR_USD');
  });

  it('should provide pagination selector', () => {
    const { result } = renderHook(() => useCrossoverStore(state => state.currentPage));

    expect(result.current).toBe(1);

    act(() => {
      useCrossoverStore.getState().setCurrentPage(2);
    });

    expect(result.current).toBe(2);
  });
});

'use client';

import { Crossover } from '@/types';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

interface CrossoverFilters {
  pairs: string[];
  timeframes: string[];
  signalTypes: ('BULLISH' | 'BEARISH')[];
  dateRange?: {
    start: Date;
    end: Date;
  };
}

interface CrossoverSorting {
  field: 'timestamp' | 'pair' | 'price' | 'crossoverType';
  direction: 'asc' | 'desc';
}

interface CrossoverState {
  // Data state
  crossovers: Crossover[];
  loading: boolean;
  error: string | null;
  isEmpty: boolean;
  lastFetched: Date | null;

  // UI state
  filters: CrossoverFilters;
  sorting: CrossoverSorting;
  searchQuery: string;

  // Pagination
  currentPage: number;
  itemsPerPage: number;
  totalItems: number;

  // Actions
  setCrossovers: (crossovers: Crossover[]) => void;
  addCrossover: (crossover: Crossover) => void;
  updateCrossover: (id: string, updates: Partial<Crossover>) => void;
  removeCrossover: (id: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setIsEmpty: (isEmpty: boolean) => void;
  setLastFetched: (date: Date) => void;

  // Filter actions
  setFilters: (filters: Partial<CrossoverFilters>) => void;
  resetFilters: () => void;
  togglePairFilter: (pair: string) => void;
  toggleTimeframeFilter: (timeframe: string) => void;
  toggleSignalTypeFilter: (signalType: 'BULLISH' | 'BEARISH') => void;

  // Sorting actions
  setSorting: (sorting: CrossoverSorting) => void;
  toggleSortDirection: () => void;

  // Search actions
  setSearchQuery: (query: string) => void;

  // Pagination actions
  setCurrentPage: (page: number) => void;
  setItemsPerPage: (itemsPerPage: number) => void;

  // Utility actions
  getFilteredCrossovers: () => Crossover[];
  reset: () => void;
}

const initialFilters: CrossoverFilters = {
  pairs: [],
  timeframes: [],
  signalTypes: [],
};

const initialSorting: CrossoverSorting = {
  field: 'timestamp',
  direction: 'desc',
};

const initialState = {
  crossovers: [],
  loading: false,
  error: null,
  isEmpty: false,
  lastFetched: null,
  filters: initialFilters,
  sorting: initialSorting,
  searchQuery: '',
  currentPage: 1,
  itemsPerPage: 20,
  totalItems: 0,
};

export const useCrossoverStore = create<CrossoverState>()(
  devtools(
    persist(
      immer((set, get) => ({
        ...initialState,

        setCrossovers: (crossovers: Crossover[]) =>
          set(state => {
            state.crossovers = crossovers;
            state.totalItems = crossovers.length;
            state.isEmpty = crossovers.length === 0;
            state.error = null;
          }),

        addCrossover: (crossover: Crossover) =>
          set(state => {
            // Add to beginning for most recent first
            state.crossovers.unshift(crossover);
            state.totalItems = state.crossovers.length;
            state.isEmpty = false;
          }),

        updateCrossover: (id: string, updates: Partial<Crossover>) =>
          set(state => {
            const index = state.crossovers.findIndex(c => c._id === id);
            if (index !== -1) {
              state.crossovers[index] = { ...state.crossovers[index], ...updates };
            }
          }),

        removeCrossover: (id: string) =>
          set(state => {
            state.crossovers = state.crossovers.filter(c => c._id !== id);
            state.totalItems = state.crossovers.length;
            state.isEmpty = state.crossovers.length === 0;
          }),

        setLoading: (loading: boolean) =>
          set(state => {
            state.loading = loading;
          }),

        setError: (error: string | null) =>
          set(state => {
            state.error = error;
          }),

        setIsEmpty: (isEmpty: boolean) =>
          set(state => {
            state.isEmpty = isEmpty;
          }),

        setLastFetched: (date: Date) =>
          set(state => {
            state.lastFetched = date;
          }),

        setFilters: (filters: Partial<CrossoverFilters>) =>
          set(state => {
            state.filters = { ...state.filters, ...filters };
            state.currentPage = 1; // Reset to first page when filters change
          }),

        resetFilters: () =>
          set(state => {
            state.filters = initialFilters;
            state.currentPage = 1;
          }),

        togglePairFilter: (pair: string) =>
          set(state => {
            const pairs = state.filters.pairs;
            if (pairs.includes(pair)) {
              state.filters.pairs = pairs.filter(p => p !== pair);
            } else {
              state.filters.pairs.push(pair);
            }
            state.currentPage = 1;
          }),

        toggleTimeframeFilter: (timeframe: string) =>
          set(state => {
            const timeframes = state.filters.timeframes;
            if (timeframes.includes(timeframe)) {
              state.filters.timeframes = timeframes.filter(t => t !== timeframe);
            } else {
              state.filters.timeframes.push(timeframe);
            }
            state.currentPage = 1;
          }),

        toggleSignalTypeFilter: (signalType: 'BULLISH' | 'BEARISH') =>
          set(state => {
            const signalTypes = state.filters.signalTypes;
            if (signalTypes.includes(signalType)) {
              state.filters.signalTypes = signalTypes.filter(s => s !== signalType);
            } else {
              state.filters.signalTypes.push(signalType);
            }
            state.currentPage = 1;
          }),

        setSorting: (sorting: CrossoverSorting) =>
          set(state => {
            state.sorting = sorting;
          }),

        toggleSortDirection: () =>
          set(state => {
            state.sorting.direction = state.sorting.direction === 'asc' ? 'desc' : 'asc';
          }),

        setSearchQuery: (query: string) =>
          set(state => {
            state.searchQuery = query;
            state.currentPage = 1; // Reset to first page when search changes
          }),

        setCurrentPage: (page: number) =>
          set(state => {
            state.currentPage = page;
          }),

        setItemsPerPage: (itemsPerPage: number) =>
          set(state => {
            state.itemsPerPage = itemsPerPage;
            state.currentPage = 1; // Reset to first page when page size changes
          }),

        getFilteredCrossovers: () => {
          const state = get();
          let filtered = [...state.crossovers];

          // Apply filters
          if (state.filters.pairs.length > 0) {
            filtered = filtered.filter(c => state.filters.pairs.includes(c.pair));
          }

          if (state.filters.timeframes.length > 0) {
            filtered = filtered.filter(c => state.filters.timeframes.includes(c.timeframe));
          }

          if (state.filters.signalTypes.length > 0) {
            filtered = filtered.filter(c => state.filters.signalTypes.includes(c.crossoverType));
          }

          if (state.filters.dateRange) {
            filtered = filtered.filter(c => {
              const crossoverDate = new Date(c.timestamp);
              return (
                crossoverDate >= state.filters.dateRange!.start &&
                crossoverDate <= state.filters.dateRange!.end
              );
            });
          }

          // Apply search
          if (state.searchQuery) {
            const query = state.searchQuery.toLowerCase();
            filtered = filtered.filter(
              c =>
                c.pair.toLowerCase().includes(query) ||
                c.crossoverType.toLowerCase().includes(query) ||
                c.timeframe.toLowerCase().includes(query)
            );
          }

          // Apply sorting
          filtered.sort((a, b) => {
            let aValue: any;
            let bValue: any;

            switch (state.sorting.field) {
              case 'timestamp':
                aValue = new Date(a.timestamp);
                bValue = new Date(b.timestamp);
                break;
              case 'pair':
                aValue = a.pair;
                bValue = b.pair;
                break;
              case 'price':
                aValue = parseFloat(a.price);
                bValue = parseFloat(b.price);
                break;
              case 'crossoverType':
                aValue = a.crossoverType;
                bValue = b.crossoverType;
                break;
              default:
                return 0;
            }

            if (aValue < bValue) return state.sorting.direction === 'asc' ? -1 : 1;
            if (aValue > bValue) return state.sorting.direction === 'asc' ? 1 : -1;
            return 0;
          });

          return filtered;
        },

        reset: () =>
          set(state => {
            Object.assign(state, initialState);
          }),
      })),
      {
        name: 'crossover-store',
        // Persist user preferences but not the actual data
        partialize: state => ({
          filters: state.filters,
          sorting: state.sorting,
          itemsPerPage: state.itemsPerPage,
        }),
      }
    ),
    {
      name: 'crossover-store',
    }
  )
);

// Selectors for common use cases
export const useCrossovers = () => useCrossoverStore(state => state.crossovers);
export const useCrossoverLoading = () => useCrossoverStore(state => state.loading);
export const useCrossoverError = () => useCrossoverStore(state => state.error);
export const useCrossoverFilters = () => useCrossoverStore(state => state.filters);
export const useCrossoverSorting = () => useCrossoverStore(state => state.sorting);
export const useFilteredCrossovers = () =>
  useCrossoverStore(state => state.getFilteredCrossovers());
export const useCrossoverPagination = () =>
  useCrossoverStore(state => ({
    currentPage: state.currentPage,
    itemsPerPage: state.itemsPerPage,
    totalItems: state.totalItems,
  }));

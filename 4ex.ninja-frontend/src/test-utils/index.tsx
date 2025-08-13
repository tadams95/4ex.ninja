import { config } from '@/lib/wagmi';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, RenderOptions } from '@testing-library/react';
import React, { ReactElement } from 'react';
import { WagmiProvider } from 'wagmi';

// Mock wallet connection for testing
export const mockWalletAddress = '0x1234567890123456789012345678901234567890';

// Mock useAccount hook for testing
export const mockUseAccount = {
  address: mockWalletAddress,
  isConnected: true,
  isConnecting: false,
  isDisconnected: false,
  chain: { id: 1, name: 'Ethereum' },
};

// Create a test wrapper for React Query
export const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });

// Test wrapper that provides all necessary contexts
export const TestWrapper = ({
  children,
  mockAccount = mockUseAccount,
}: {
  children: React.ReactNode;
  mockAccount?: any;
}) => {
  const queryClient = createTestQueryClient();

  // Mock wagmi hooks for testing
  jest.mock('wagmi', () => ({
    ...jest.requireActual('wagmi'),
    useAccount: () => mockAccount,
    useDisconnect: () => ({ disconnect: jest.fn() }),
  }));

  return (
    <QueryClientProvider client={queryClient}>
      <WagmiProvider config={config}>{children}</WagmiProvider>
    </QueryClientProvider>
  );
};

// Create a custom render function that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  // Create a new QueryClient for each test to ensure isolation
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Disable retries in tests
        staleTime: Infinity, // Keep data fresh during tests
      },
    },
  });

  return (
    <SessionProvider session={mockSession}>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </SessionProvider>
  );
};

const customRender = (ui: ReactElement, options?: Omit<RenderOptions, 'wrapper'>) =>
  render(ui, { wrapper: AllTheProviders, ...options });

// Re-export everything
export * from '@testing-library/react';

// Override render method
export { customRender as render };

// Additional test utilities
export const createMockUser = (overrides = {}) => ({
  id: 'test-user-123',
  name: 'Test User',
  email: 'test@example.com',
  isSubscribed: true,
  subscriptionStatus: 'active',
  subscriptionEnds: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
  ...overrides,
});

export const createMockCrossover = (overrides = {}) => ({
  id: 'test-crossover-123',
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

export const waitForLoadingToFinish = () => new Promise(resolve => setTimeout(resolve, 0));

// Mock router push function for testing navigation
export const mockRouterPush = jest.fn();

// Reset all mocks between tests
export const resetAllMocks = () => {
  mockRouterPush.mockClear();
  jest.clearAllMocks();
};

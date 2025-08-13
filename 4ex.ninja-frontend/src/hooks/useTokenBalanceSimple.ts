'use client';

import { TOKEN_CONFIG, calculateAccessTier, type AccessTier } from '@/lib/token';
import { useQuery } from '@tanstack/react-query';
import { useAccount } from 'wagmi';

interface TokenBalanceResult {
  balance: bigint;
  tier: AccessTier;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

/**
 * Fetch token balance via our API route (avoids CORS issues)
 */
async function fetchTokenBalanceViaAPI(walletAddress: string): Promise<bigint> {
  console.log(`fetchTokenBalanceViaAPI called with address: ${walletAddress}`);

  try {
    const response = await fetch(`/api/token-balance?address=${walletAddress}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log(`API Response status: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      const errorData = await response.json();
      console.error('API Error:', errorData);
      throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    console.log('API Response:', result);

    if (!result.success || !result.balance) {
      throw new Error('Invalid API response format');
    }

    // Convert hex result to bigint
    const balance = BigInt(result.balance);
    console.log(`Success: Balance = ${balance.toString()}`);
    return balance;
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}

/**
 * Hook to get user's $4EX token balance and access tier
 * Uses direct RPC calls for maximum reliability
 */
export function useTokenBalance(): TokenBalanceResult {
  const { address, isConnected, chain } = useAccount();

  const {
    data: balance = BigInt(0),
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['tokenBalance', address, chain?.id],
    queryFn: async (): Promise<bigint> => {
      if (!address) {
        console.log('useTokenBalance: No wallet address provided');
        return BigInt(0);
      }

      // Check if we're on the right network
      if (chain?.id !== TOKEN_CONFIG.chainId) {
        console.warn(
          `useTokenBalance: Wrong network. Expected ${TOKEN_CONFIG.chainId} (Base), got ${chain?.id}`
        );
        throw new Error(`Please switch to Base network (Chain ID: ${TOKEN_CONFIG.chainId})`);
      }

      console.log('useTokenBalance: Fetching balance for', address);
      console.log('useTokenBalance: Token contract', TOKEN_CONFIG.address);
      console.log('useTokenBalance: Chain', chain);

      try {
        return await fetchTokenBalanceViaAPI(address);
      } catch (error: any) {
        console.error('useTokenBalance: Error fetching balance:', error);
        throw new Error(`Failed to fetch token balance: ${error.message || 'Unknown error'}`);
      }
    },
    enabled: isConnected && !!address && chain?.id === TOKEN_CONFIG.chainId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: 30 * 1000, // 30 seconds
    retry: (failureCount, error: any) => {
      // Don't retry if it's a network/chain issue
      if (error?.message?.includes('Please switch to Base network')) {
        return false;
      }
      // Retry up to 3 times for other errors
      return failureCount < 3;
    },
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  const tier = calculateAccessTier(balance);

  return {
    balance,
    tier,
    isLoading,
    error: error as Error | null,
    refetch,
  };
}

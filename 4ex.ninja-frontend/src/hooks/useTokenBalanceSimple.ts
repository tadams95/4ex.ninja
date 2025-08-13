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
 * Direct RPC call to fetch token balance
 * Using the same approach as the successful curl command
 */
async function fetchTokenBalanceDirect(walletAddress: string): Promise<bigint> {
  // ERC20 balanceOf function selector: 0x70a08231
  // Encode the wallet address (remove 0x prefix and pad to 32 bytes)
  const paddedAddress = walletAddress.slice(2).toLowerCase().padStart(64, '0');
  const data = `0x70a08231${paddedAddress}`;

  const rpcPayload = {
    jsonrpc: '2.0',
    method: 'eth_call',
    params: [
      {
        to: TOKEN_CONFIG.address,
        data: data,
      },
      'latest',
    ],
    id: 1,
  };

  // Try multiple RPC endpoints
  const rpcEndpoints = [
    'https://mainnet.base.org',
    'https://base.llamarpc.com',
    'https://1rpc.io/base',
    'https://base.blockpi.network/v1/rpc/public',
  ];

  for (const endpoint of rpcEndpoints) {
    try {
      console.log(`Trying RPC endpoint: ${endpoint}`);
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(rpcPayload),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      if (result.error) {
        throw new Error(`RPC Error: ${result.error.message || result.error}`);
      }

      if (!result.result) {
        throw new Error('No result returned from RPC call');
      }

      // Convert hex result to bigint
      const balance = BigInt(result.result);
      console.log(`Success with ${endpoint}: Balance = ${balance.toString()}`);
      return balance;
    } catch (error) {
      console.warn(`RPC endpoint ${endpoint} failed:`, error);
      continue;
    }
  }

  throw new Error('All RPC endpoints failed to fetch token balance');
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
        console.warn(`useTokenBalance: Wrong network. Expected ${TOKEN_CONFIG.chainId} (Base), got ${chain?.id}`);
        throw new Error(`Please switch to Base network (Chain ID: ${TOKEN_CONFIG.chainId})`);
      }

      console.log('useTokenBalance: Fetching balance for', address);
      console.log('useTokenBalance: Token contract', TOKEN_CONFIG.address);
      console.log('useTokenBalance: Chain', chain);

      try {
        return await fetchTokenBalanceDirect(address);
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

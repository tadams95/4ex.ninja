'use client';

import { TOKEN_CONFIG, calculateAccessTier, type AccessTier } from '@/lib/token';
import { wagmiConfig } from '@/lib/wagmi';
import { useQuery } from '@tanstack/react-query';
import { createConfig, http, useAccount } from 'wagmi';
import { readContract } from 'wagmi/actions';
import { base } from 'wagmi/chains';

// ERC20 ABI for balanceOf function
const ERC20_ABI = [
  {
    constant: true,
    inputs: [{ name: '_owner', type: 'address' }],
    name: 'balanceOf',
    outputs: [{ name: 'balance', type: 'uint256' }],
    type: 'function',
  },
] as const;

// Fallback RPC endpoints for Base network (from Base docs + reliable providers)
const BASE_RPC_ENDPOINTS = [
  'https://mainnet.base.org', // Official Base RPC
  'https://base.llamarpc.com', // LlamaNodes
  'https://base.blockpi.network/v1/rpc/public', // BlockPI
  'https://1rpc.io/base', // 1RPC
  'https://base-mainnet.public.blastapi.io', // Blast API
  'https://base.drpc.org', // dRPC
  'https://gateway.tenderly.co/public/base', // Tenderly
];

/**
 * Try multiple RPC endpoints to fetch token balance
 */
async function fetchTokenBalanceWithFallback(address: string): Promise<bigint> {
  const errors: Error[] = [];

  for (const rpcUrl of BASE_RPC_ENDPOINTS) {
    try {
      console.log(`useTokenBalance: Trying RPC endpoint: ${rpcUrl}`);

      // Create a temporary config for this RPC endpoint
      const tempConfig = createConfig({
        chains: [base],
        connectors: [],
        transports: {
          [base.id]: http(rpcUrl),
        },
      });

      const result = await readContract(tempConfig, {
        address: TOKEN_CONFIG.address,
        abi: ERC20_ABI,
        functionName: 'balanceOf',
        args: [address],
        chainId: TOKEN_CONFIG.chainId,
      });

      const balance = result as bigint;
      console.log(`useTokenBalance: Success with ${rpcUrl}, balance:`, balance.toString());
      return balance;
    } catch (error: any) {
      console.warn(`useTokenBalance: RPC endpoint ${rpcUrl} failed:`, error?.message);
      errors.push(error);
      continue;
    }
  }

  // If all endpoints failed, throw the last error
  console.error('useTokenBalance: All RPC endpoints failed:', errors);
  throw new Error(
    `All RPC endpoints failed. Last error: ${errors[errors.length - 1]?.message || 'Unknown error'}`
  );
}

interface TokenBalanceResult {
  balance: bigint;
  tier: AccessTier;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

/**
 * Hook to get user's $4EX token balance and access tier
 * Includes caching and automatic refetching with fallback handling
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
        console.log('useTokenBalance: No address provided');
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
      console.log('useTokenBalance: Token config', TOKEN_CONFIG);
      console.log('useTokenBalance: Current chain', chain);

      try {
        // First try the main wagmi config
        console.log('useTokenBalance: Trying main wagmi config...');

        const result = await readContract(wagmiConfig, {
          address: TOKEN_CONFIG.address,
          abi: ERC20_ABI,
          functionName: 'balanceOf',
          args: [address],
          chainId: TOKEN_CONFIG.chainId,
        });

        const balance = result as bigint;
        console.log(
          'useTokenBalance: Balance fetched successfully with main config',
          balance.toString()
        );
        return balance;
      } catch (mainError: any) {
        console.warn(
          'useTokenBalance: Main config failed, trying fallback RPC endpoints...',
          mainError?.message
        );

        try {
          return await fetchTokenBalanceWithFallback(address);
        } catch (fallbackError: any) {
          console.error('useTokenBalance: Both main and fallback methods failed:', {
            mainError: mainError?.message,
            fallbackError: fallbackError?.message,
          });

          // Provide more specific error messages
          if (fallbackError?.message?.includes('All RPC endpoints failed')) {
            throw new Error(
              'Unable to connect to Base network. All RPC endpoints are unavailable.'
            );
          }
          if (fallbackError?.message?.includes('execution reverted')) {
            throw new Error(
              'Contract call reverted. The token contract might not exist at this address.'
            );
          }

          throw new Error(
            `Contract call failed: ${
              fallbackError instanceof Error ? fallbackError.message : 'Unknown error'
            }`
          );
        }
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

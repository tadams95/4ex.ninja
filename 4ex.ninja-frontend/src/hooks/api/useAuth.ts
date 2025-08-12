'use client';

import { useAccount } from 'wagmi';

// Query keys for auth-related queries
export const authKeys = {
  all: ['auth'] as const,
  session: () => [...authKeys.all, 'session'] as const,
  user: () => [...authKeys.all, 'user'] as const,
} as const;

interface AuthState {
  isAuthenticated: boolean;
  user: { address: string } | null;
  loading: boolean;
}

// use wagmi's wallet connection as authentication
export const useAuth = (): AuthState => {
  const { isConnected, address, isConnecting } = useAccount();
  return {
    isAuthenticated: isConnected,
    user: address ? { address } : null,
    loading: isConnecting,
  };
};

// All session/query-based hooks removed; only wallet-based useAuth remains.

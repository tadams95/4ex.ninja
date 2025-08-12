'use client';

import { BaseComponentProps, User } from '@/types';
import { createContext, useContext, useEffect, useState } from 'react';
import { useAccount } from 'wagmi';

interface AuthContextType {
  isAuthenticated: boolean;
  isSubscribed: boolean;
  loading: boolean;
  user: User | null;
}

interface AuthProviderProps extends BaseComponentProps {}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  isSubscribed: false,
  loading: true,
  user: null,
});

export function AuthProvider({ children }: AuthProviderProps) {
  const { isConnected, address, isConnecting } = useAccount();
  const [isSubscribed, setIsSubscribed] = useState<boolean>(false);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    if (isConnected && address) {
      // Create a user object from wallet connection
      const walletUser: User = {
        id: address,
        email: '', // Will be populated from API if available
        name: '', // Will be populated from API if available
        walletAddress: address,
        isSubscribed: false, // Will be checked from API
      };
      setUser(walletUser);

      // Check subscription status from API
      // This would typically make an API call to check user's subscription
      setIsSubscribed(false); // Default to false
    } else {
      setUser(null);
      setIsSubscribed(false);
    }
  }, [isConnected, address]);

  const value: AuthContextType = {
    isAuthenticated: isConnected,
    isSubscribed,
    loading: isConnecting,
    user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = (): AuthContextType => useContext(AuthContext);

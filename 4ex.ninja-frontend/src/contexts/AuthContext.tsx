'use client';

import { BaseComponentProps, User } from '@/types';
import { useSession } from 'next-auth/react';
import { createContext, useContext, useEffect, useState } from 'react';

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
  const { data: session, status } = useSession();
  const [isSubscribed, setIsSubscribed] = useState<boolean>(false);

  useEffect(() => {
    if (session?.user) {
      // Check if user has an active subscription
      const user = session.user as User;
      const subscriptionEnds = user.subscriptionEnds ? new Date(user.subscriptionEnds) : null;

      const isActive = subscriptionEnds && subscriptionEnds > new Date();
      setIsSubscribed(!!isActive);
    } else {
      setIsSubscribed(false);
    }
  }, [session]);

  const value: AuthContextType = {
    isAuthenticated: !!session,
    isSubscribed,
    loading: status === 'loading',
    user: (session?.user as User) || null,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = (): AuthContextType => useContext(AuthContext);

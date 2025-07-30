'use client';
import { BaseComponentProps } from '@/types';
import { SessionProvider } from 'next-auth/react';

interface AuthProviderProps extends BaseComponentProps {}

export function AuthProvider({ children }: AuthProviderProps) {
  return <SessionProvider refetchInterval={5 * 60}>{children}</SessionProvider>;
}

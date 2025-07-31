'use client';
import { AuthProviderErrorBoundary } from '@/components/error';
import { BaseComponentProps } from '@/types';
import { SessionProvider } from 'next-auth/react';

interface AuthProviderProps extends BaseComponentProps {}

function AuthProviderComponent({ children }: AuthProviderProps) {
  return <SessionProvider refetchInterval={5 * 60}>{children}</SessionProvider>;
}

export function AuthProvider({ children }: AuthProviderProps) {
  return (
    <AuthProviderErrorBoundary>
      <AuthProviderComponent>{children}</AuthProviderComponent>
    </AuthProviderErrorBoundary>
  );
}

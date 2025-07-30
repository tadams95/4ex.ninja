'use client';

import { AuthProvider } from '@/contexts/AuthContext';
import { BaseComponentProps } from '@/types';
import { SessionProvider } from 'next-auth/react';

interface ProvidersProps extends BaseComponentProps {}

export default function Providers({ children }: ProvidersProps) {
  return (
    <SessionProvider>
      <AuthProvider>{children}</AuthProvider>
    </SessionProvider>
  );
}

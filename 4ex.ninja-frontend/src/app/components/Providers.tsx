'use client';

import { ErrorNotificationProvider } from '@/components/error/ErrorNotificationSystem';
import ProvidersErrorBoundary from '@/components/error/ProvidersErrorBoundary';
import { AuthProvider } from '@/contexts/AuthContext';
import { BaseComponentProps } from '@/types';
import { SessionProvider } from 'next-auth/react';

interface ProvidersProps extends BaseComponentProps {}

function ProvidersComponent({ children }: ProvidersProps) {
  return (
    <SessionProvider>
      <AuthProvider>
        <ErrorNotificationProvider>{children}</ErrorNotificationProvider>
      </AuthProvider>
    </SessionProvider>
  );
}

export default function Providers({ children }: ProvidersProps) {
  return (
    <ProvidersErrorBoundary>
      <ProvidersComponent>{children}</ProvidersComponent>
    </ProvidersErrorBoundary>
  );
}

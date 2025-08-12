'use client';

import { ErrorNotificationProvider } from '@/components/error/ErrorNotificationSystem';
import ProvidersErrorBoundary from '@/components/error/ProvidersErrorBoundary';
import { AuthProvider } from '@/contexts/AuthContext';
import { queryClient } from '@/lib/queryClient';
import { wagmiConfig } from '@/lib/wagmi';
import { BaseComponentProps } from '@/types';
import { initializeServiceWorker } from '@/utils/service-worker';
import { OnchainKitProvider } from '@coinbase/onchainkit';
import { QueryClientProvider } from '@tanstack/react-query';
import { SessionProvider } from 'next-auth/react';
import dynamic from 'next/dynamic';
import { useEffect } from 'react';
import { WagmiProvider } from 'wagmi';
import { base } from 'wagmi/chains';

// Lazy load React Query devtools only in development
const ReactQueryDevtools = dynamic(
  () =>
    import('@tanstack/react-query-devtools').then(mod => ({
      default: mod.ReactQueryDevtools,
    })),
  {
    ssr: false,
    loading: () => null, // No loading state needed for devtools
  }
);

interface ProvidersProps extends BaseComponentProps {}

function ProvidersComponent({ children }: ProvidersProps) {
  // Initialize service worker for asset optimization
  useEffect(() => {
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
      initializeServiceWorker().catch(error => {
        console.error('Failed to initialize service worker:', error);
      });
    }
  }, []);

  return (
    <OnchainKitProvider
      apiKey={process.env.NEXT_PUBLIC_ONCHAINKIT_API_KEY}
      chain={base}
      config={{
        appearance: {
          mode: 'dark',
          theme: 'dark',
        },
      }}
    >
      <WagmiProvider config={wagmiConfig}>
        <QueryClientProvider client={queryClient}>
          <SessionProvider>
            <AuthProvider>
              <ErrorNotificationProvider>
                {children}
                {/* Only show devtools in development */}
                {process.env.NODE_ENV === 'development' && (
                  <ReactQueryDevtools initialIsOpen={false} />
                )}
              </ErrorNotificationProvider>
            </AuthProvider>
          </SessionProvider>
        </QueryClientProvider>
      </WagmiProvider>
    </OnchainKitProvider>
  );
}

export default function Providers({ children }: ProvidersProps) {
  return (
    <ProvidersErrorBoundary>
      <ProvidersComponent>{children}</ProvidersComponent>
    </ProvidersErrorBoundary>
  );
}

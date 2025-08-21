'use client';

import { ErrorNotificationProvider } from '@/components/error/ErrorNotificationSystem';
import { OnchainKitErrorBoundary } from '@/components/error/OnchainKitErrorBoundary';
import ProvidersErrorBoundary from '@/components/error/ProvidersErrorBoundary';
import { AuthProvider } from '@/contexts/AuthContext';
import { queryClient } from '@/lib/queryClient';
import { wagmiConfig } from '@/lib/wagmi';
import { BaseComponentProps } from '@/types';
import { initializeServiceWorker } from '@/utils/service-worker';
import { OnchainKitProvider } from '@coinbase/onchainkit';
import '@coinbase/onchainkit/styles.css';
import { QueryClientProvider } from '@tanstack/react-query';
import dynamic from 'next/dynamic';
import { useEffect } from 'react';
import { WagmiProvider } from 'wagmi';
import { base } from 'wagmi/chains';

// Lazy load React Query devtools only in development
const ReactQueryDevtools = dynamic(
  () => import('@tanstack/react-query-devtools').then(mod => mod.ReactQueryDevtools),
  {
    ssr: false,
    loading: () => null, // No loading state needed for devtools
  }
);

interface ProvidersProps extends BaseComponentProps {}

function ProvidersComponent({ children }: ProvidersProps) {
  // Initialize service worker for asset optimization
  useEffect(() => {
    if (typeof window !== 'undefined') {
      if (process.env.NODE_ENV === 'production') {
        initializeServiceWorker().catch(error => {
          console.error('Failed to initialize service worker:', error);
        });
      } else {
        // In development, unregister any existing service workers to prevent interference
        if ('serviceWorker' in navigator) {
          navigator.serviceWorker.getRegistrations().then(registrations => {
            registrations.forEach(registration => {
              registration.unregister();
              console.log('[Dev] Unregistered service worker:', registration.scope);
            });
          });
        }
      }
    }
  }, []);

  return (
    <OnchainKitErrorBoundary>
      <OnchainKitProvider
        apiKey={process.env.NEXT_PUBLIC_ONCHAINKIT_API_KEY}
        chain={base}
        config={{
          appearance: {
            mode: 'dark',
            theme: 'custom',
          },
          wallet: {
            display: 'classic',
          },
        }}
        schemaId="0xf8b05c79f090979bf4a80270aba232dff11a10d9ca55c4f88de95317970f0de9"
      >
        <WagmiProvider config={wagmiConfig}>
          <QueryClientProvider client={queryClient}>
            <AuthProvider>
              <ErrorNotificationProvider>
                {children}
                {/* Only show devtools in development */}
                {process.env.NODE_ENV === 'development' && (
                  <ReactQueryDevtools initialIsOpen={false} />
                )}
              </ErrorNotificationProvider>
            </AuthProvider>
          </QueryClientProvider>
        </WagmiProvider>
      </OnchainKitProvider>
    </OnchainKitErrorBoundary>
  );
}

export default function Providers({ children }: ProvidersProps) {
  return (
    <ProvidersErrorBoundary>
      <ProvidersComponent>{children}</ProvidersComponent>
    </ProvidersErrorBoundary>
  );
}

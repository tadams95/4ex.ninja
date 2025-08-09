'use client';

// Lazy-loaded component for Account page to reduce main bundle size
import { LoadingSequence } from '@/components/ui';
import dynamic from 'next/dynamic';
import { Suspense } from 'react';

// Lazy load the main account component with loading state
const AccountPageComponent = dynamic(() => import('./AccountPageComponent'), {
  loading: () => <LoadingSequence type="auth" />,
  ssr: false, // Disable SSR for this heavy component
});

export default function AccountPage() {
  return (
    <Suspense fallback={<LoadingSequence type="auth" />}>
      <AccountPageComponent />
    </Suspense>
  );
}

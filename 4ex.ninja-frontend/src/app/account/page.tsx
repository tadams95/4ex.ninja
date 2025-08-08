'use client';

// Lazy-loaded component for Account page to reduce main bundle size
import dynamic from 'next/dynamic';
import { Suspense } from 'react';

// Lazy load the main account component with loading state
const AccountPageComponent = dynamic(() => import('./AccountPageComponent'), {
  loading: () => (
    <div className="container mx-auto px-4 py-8 max-w-2xl bg-black min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
        <p className="mt-2">Loading account...</p>
      </div>
    </div>
  ),
  ssr: false, // Disable SSR for this heavy component
});

export default function AccountPage() {
  return (
    <Suspense
      fallback={
        <div className="container mx-auto px-4 py-8 max-w-2xl bg-black min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
            <p className="mt-2">Loading account...</p>
          </div>
        </div>
      }
    >
      <AccountPageComponent />
    </Suspense>
  );
}

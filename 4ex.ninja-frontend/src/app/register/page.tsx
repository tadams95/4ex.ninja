'use client';

// Lazy-loaded component for Register page to reduce main bundle size
import dynamic from 'next/dynamic';
import { Suspense } from 'react';

// Lazy load the main register component with loading state
const RegisterPageComponent = dynamic(() => import('./RegisterPageComponent'), {
  loading: () => (
    <div className="container mx-auto px-4 py-8 max-w-2xl bg-black min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
        <p className="mt-2">Loading registration...</p>
      </div>
    </div>
  ),
  ssr: false, // Disable SSR for this component with heavy validation logic
});

export default function RegisterPage() {
  return (
    <Suspense
      fallback={
        <div className="container mx-auto px-4 py-8 max-w-2xl bg-black min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
            <p className="mt-2">Loading registration...</p>
          </div>
        </div>
      }
    >
      <RegisterPageComponent />
    </Suspense>
  );
}

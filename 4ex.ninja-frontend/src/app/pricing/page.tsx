'use client';

// Lazy-loaded component for Pricing page to reduce main bundle size
import dynamic from 'next/dynamic';
import { Suspense } from 'react';

// Lazy load the main pricing component with loading state
const PricingPageComponent = dynamic(() => import('./PricingPageComponent'), {
  loading: () => (
    <div className="container mx-auto px-4 py-8 max-w-2xl bg-black min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
        <p className="mt-2">Loading pricing...</p>
      </div>
    </div>
  ),
  ssr: false, // Disable SSR for this heavy component with Stripe integration
});

export default function PricingPage() {
  return (
    <Suspense
      fallback={
        <div className="container mx-auto px-4 py-8 max-w-2xl bg-black min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
            <p className="mt-2">Loading pricing...</p>
          </div>
        </div>
      }
    >
      <PricingPageComponent />
    </Suspense>
  );
}

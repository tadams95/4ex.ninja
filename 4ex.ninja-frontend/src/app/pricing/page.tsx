'use client';

// Lazy-loaded component for Pricing page to reduce main bundle size
import dynamic from 'next/dynamic';
import { Suspense } from 'react';
import { PricingCardSkeleton } from '@/components/ui';

// Lazy load the main pricing component with loading state
const PricingPageComponent = dynamic(() => import('./PricingPageComponent'), {
  loading: () => (
    <div className="container mx-auto px-4 py-8 max-w-4xl bg-black min-h-screen">
      <h1 className="text-3xl font-bold text-center mb-8">Choose Your Plan</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(3)].map((_, i) => (
          <PricingCardSkeleton key={i} />
        ))}
      </div>
    </div>
  ),
  ssr: false, // Disable SSR for this heavy component with Stripe integration
});

export default function PricingPage() {
  return (
    <Suspense
      fallback={
        <div className="container mx-auto px-4 py-8 max-w-4xl bg-black min-h-screen">
          <h1 className="text-3xl font-bold text-center mb-8">Choose Your Plan</h1>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(3)].map((_, i) => (
              <PricingCardSkeleton key={i} />
            ))}
          </div>
        </div>
      }
    >
      <PricingPageComponent />
    </Suspense>
  );
}

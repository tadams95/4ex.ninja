'use client';

// Lazy-loaded component for Register page to reduce main bundle size
import dynamic from 'next/dynamic';
import { Suspense } from 'react';
import { FormSkeleton } from '@/components/ui';

// Lazy load the main register component with loading state
const RegisterPageComponent = dynamic(() => import('./RegisterPageComponent'), {
  loading: () => (
    <div className="container mx-auto px-4 py-8 max-w-md bg-black min-h-screen flex items-center justify-center">
      <div className="bg-gray-800 rounded-lg p-6 w-full">
        <h2 className="text-2xl font-bold text-center mb-6">Create Account</h2>
        <FormSkeleton fields={4} />
      </div>
    </div>
  ),
  ssr: false, // Disable SSR for this component with heavy validation logic
});

export default function RegisterPage() {
  return (
    <Suspense
      fallback={
        <div className="container mx-auto px-4 py-8 max-w-md bg-black min-h-screen flex items-center justify-center">
          <div className="bg-gray-800 rounded-lg p-6 w-full">
            <h2 className="text-2xl font-bold text-center mb-6">Create Account</h2>
            <FormSkeleton fields={4} />
          </div>
        </div>
      }
    >
      <RegisterPageComponent />
    </Suspense>
  );
}

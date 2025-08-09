/**
 * Skeleton Loading Components
 * 
 * Provides skeleton loading states for async components to improve perceived performance.
 * Uses CSS animations for smooth loading effects.
 */

import React from 'react';

interface SkeletonProps {
  className?: string;
  children?: React.ReactNode;
}

// Base skeleton component with shimmer animation
export const Skeleton: React.FC<SkeletonProps> = ({ className = '', children }) => (
  <div
    className={`animate-pulse bg-gray-700 rounded ${className}`}
    aria-label="Loading..."
    role="status"
  >
    {children}
  </div>
);

// Skeleton for crossover/signal items in the feed
export const CrossoverSkeleton: React.FC = () => (
  <div className="bg-gray-800 rounded-lg p-4 mb-4">
    <div className="flex justify-between items-start mb-2">
      <Skeleton className="h-5 w-20" /> {/* Currency pair */}
      <Skeleton className="h-4 w-16" /> {/* Timestamp */}
    </div>
    <div className="flex justify-between items-center mb-3">
      <Skeleton className="h-6 w-24" /> {/* Signal type */}
      <Skeleton className="h-8 w-12" /> {/* Direction indicator */}
    </div>
    <div className="grid grid-cols-2 gap-2 text-sm">
      <div>
        <Skeleton className="h-3 w-16 mb-1" /> {/* Label */}
        <Skeleton className="h-4 w-20" /> {/* Value */}
      </div>
      <div>
        <Skeleton className="h-3 w-16 mb-1" /> {/* Label */}
        <Skeleton className="h-4 w-20" /> {/* Value */}
      </div>
    </div>
  </div>
);

// Skeleton for feed statistics
export const FeedStatsSkeleton: React.FC = () => (
  <div className="bg-gray-800 rounded-lg p-4 mb-6 grid grid-cols-3 gap-4 text-center">
    <div>
      <Skeleton className="h-6 w-8 mx-auto mb-1" />
      <Skeleton className="h-4 w-12 mx-auto" />
    </div>
    <div>
      <Skeleton className="h-6 w-8 mx-auto mb-1" />
      <Skeleton className="h-4 w-12 mx-auto" />
    </div>
    <div>
      <Skeleton className="h-6 w-10 mx-auto mb-1" />
      <Skeleton className="h-4 w-16 mx-auto" />
    </div>
  </div>
);

// Skeleton for account/subscription information
export const AccountSkeleton: React.FC = () => (
  <div className="space-y-6">
    {/* Profile section */}
    <div className="bg-gray-800 rounded-lg p-6">
      <Skeleton className="h-6 w-32 mb-4" /> {/* Section title */}
      <div className="space-y-4">
        <div>
          <Skeleton className="h-4 w-16 mb-2" /> {/* Label */}
          <Skeleton className="h-10 w-full" /> {/* Input field */}
        </div>
        <div>
          <Skeleton className="h-4 w-16 mb-2" /> {/* Label */}
          <Skeleton className="h-10 w-full" /> {/* Input field */}
        </div>
        <Skeleton className="h-10 w-24" /> {/* Save button */}
      </div>
    </div>
    
    {/* Subscription section */}
    <div className="bg-gray-800 rounded-lg p-6">
      <Skeleton className="h-6 w-40 mb-4" /> {/* Section title */}
      <div className="space-y-3">
        <div className="flex justify-between">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-16" />
        </div>
        <div className="flex justify-between">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-20" />
        </div>
        <Skeleton className="h-10 w-32" /> {/* Action button */}
      </div>
    </div>
  </div>
);

// Skeleton for pricing cards
export const PricingCardSkeleton: React.FC = () => (
  <div className="bg-gray-800 rounded-lg p-6">
    <div className="text-center mb-6">
      <Skeleton className="h-6 w-24 mx-auto mb-2" /> {/* Plan name */}
      <Skeleton className="h-8 w-16 mx-auto mb-2" /> {/* Price */}
      <Skeleton className="h-4 w-20 mx-auto" /> {/* Billing period */}
    </div>
    <div className="space-y-3 mb-6">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="flex items-center">
          <Skeleton className="h-4 w-4 mr-2" /> {/* Checkmark */}
          <Skeleton className="h-4 flex-1" /> {/* Feature text */}
        </div>
      ))}
    </div>
    <Skeleton className="h-12 w-full" /> {/* CTA button */}
  </div>
);

// Generic form skeleton
export const FormSkeleton: React.FC<{ fields?: number }> = ({ fields = 3 }) => (
  <div className="space-y-4">
    {[...Array(fields)].map((_, i) => (
      <div key={i}>
        <Skeleton className="h-4 w-20 mb-2" /> {/* Label */}
        <Skeleton className="h-10 w-full" /> {/* Input */}
      </div>
    ))}
    <Skeleton className="h-10 w-full mt-6" /> {/* Submit button */}
  </div>
);

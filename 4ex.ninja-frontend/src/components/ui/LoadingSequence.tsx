/**
 * Optimized Loading Sequence Component
 *
 * Provides intelligent loading sequences that prioritize critical content
 * and show relevant information during authentication flows.
 */

import React, { useEffect, useState } from 'react';
import { Skeleton } from './Skeleton';

interface LoadingSequenceProps {
  type: 'auth' | 'subscription' | 'trading' | 'general';
  steps?: string[];
  currentStep?: number;
  duration?: number;
}

export const LoadingSequence: React.FC<LoadingSequenceProps> = ({
  type,
  steps,
  currentStep = 0,
  duration = 3000,
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [showContent, setShowContent] = useState(false);

  // Default steps for different flow types
  const defaultSteps = {
    auth: [
      'Verifying credentials...',
      'Loading user profile...',
      'Checking subscription...',
      'Preparing dashboard...',
    ],
    subscription: [
      'Checking payment status...',
      'Loading subscription details...',
      'Updating access permissions...',
      'Ready!',
    ],
    trading: [
      'Connecting to market data...',
      'Loading latest signals...',
      'Calculating performance...',
      'Ready to trade!',
    ],
    general: ['Loading...'],
  };

  const sequenceSteps = steps || defaultSteps[type];

  useEffect(() => {
    const stepDuration = duration / sequenceSteps.length;

    const interval = setInterval(() => {
      setActiveStep(prev => {
        if (prev < sequenceSteps.length - 1) {
          return prev + 1;
        }
        setShowContent(true);
        return prev;
      });
    }, stepDuration);

    return () => clearInterval(interval);
  }, [sequenceSteps.length, duration]);

  useEffect(() => {
    if (currentStep !== undefined) {
      setActiveStep(currentStep);
    }
  }, [currentStep]);

  const renderContent = () => {
    switch (type) {
      case 'auth':
        return <AuthLoadingContent />;
      case 'subscription':
        return <SubscriptionLoadingContent />;
      case 'trading':
        return <TradingLoadingContent />;
      default:
        return <GeneralLoadingContent />;
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl bg-black min-h-screen">
      <div className="text-center mb-8">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-green-500 mb-4"></div>
        <h2 className="text-xl font-semibold text-white mb-2">{sequenceSteps[activeStep]}</h2>

        {/* Progress bar */}
        <div className="w-full bg-gray-700 rounded-full h-2 mb-4">
          <div
            className="bg-green-500 h-2 rounded-full transition-all duration-300 ease-out"
            style={{
              width: `${((activeStep + 1) / sequenceSteps.length) * 100}%`,
            }}
          ></div>
        </div>

        {/* Step indicator */}
        <p className="text-gray-400 text-sm">
          Step {activeStep + 1} of {sequenceSteps.length}
        </p>
      </div>

      {renderContent()}
    </div>
  );
};

// Specialized loading content for authentication flows
const AuthLoadingContent: React.FC = () => (
  <div className="space-y-6">
    <div className="bg-gray-800 rounded-lg p-6">
      <Skeleton className="h-6 w-32 mb-4" />
      <div className="space-y-3">
        <div className="flex items-center space-x-3">
          <Skeleton className="h-4 w-4 rounded-full" />
          <Skeleton className="h-4 w-48" />
        </div>
        <div className="flex items-center space-x-3">
          <Skeleton className="h-4 w-4 rounded-full" />
          <Skeleton className="h-4 w-36" />
        </div>
        <div className="flex items-center space-x-3">
          <Skeleton className="h-4 w-4 rounded-full" />
          <Skeleton className="h-4 w-52" />
        </div>
      </div>
    </div>

    <div className="bg-gray-800 rounded-lg p-6">
      <Skeleton className="h-6 w-40 mb-4" />
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Skeleton className="h-4 w-16 mb-2" />
          <Skeleton className="h-8 w-full" />
        </div>
        <div>
          <Skeleton className="h-4 w-20 mb-2" />
          <Skeleton className="h-8 w-full" />
        </div>
      </div>
    </div>
  </div>
);

// Specialized loading content for subscription flows
const SubscriptionLoadingContent: React.FC = () => (
  <div className="space-y-6">
    <div className="bg-gray-800 rounded-lg p-6 text-center">
      <Skeleton className="h-8 w-24 mx-auto mb-2" />
      <Skeleton className="h-6 w-32 mx-auto mb-4" />
      <Skeleton className="h-4 w-48 mx-auto mb-6" />

      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="flex items-center justify-center space-x-2">
            <Skeleton className="h-4 w-4" />
            <Skeleton className="h-4 w-40" />
          </div>
        ))}
      </div>

      <Skeleton className="h-12 w-full mt-6" />
    </div>
  </div>
);

// Specialized loading content for trading flows
const TradingLoadingContent: React.FC = () => (
  <div className="space-y-6">
    {/* Stats skeleton */}
    <div className="bg-gray-800 rounded-lg p-4 grid grid-cols-3 gap-4 text-center">
      {[...Array(3)].map((_, i) => (
        <div key={i}>
          <Skeleton className="h-6 w-8 mx-auto mb-1" />
          <Skeleton className="h-4 w-12 mx-auto" />
        </div>
      ))}
    </div>

    {/* Signals skeleton */}
    <div className="space-y-4">
      {[...Array(3)].map((_, i) => (
        <div key={i} className="bg-gray-800 rounded-lg p-4">
          <div className="flex justify-between items-start mb-2">
            <Skeleton className="h-5 w-20" />
            <Skeleton className="h-4 w-16" />
          </div>
          <div className="flex justify-between items-center mb-3">
            <Skeleton className="h-6 w-24" />
            <Skeleton className="h-8 w-12" />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Skeleton className="h-3 w-16 mb-1" />
              <Skeleton className="h-4 w-20" />
            </div>
            <div>
              <Skeleton className="h-3 w-16 mb-1" />
              <Skeleton className="h-4 w-20" />
            </div>
          </div>
        </div>
      ))}
    </div>
  </div>
);

// General loading content
const GeneralLoadingContent: React.FC = () => (
  <div className="space-y-4">
    {[...Array(3)].map((_, i) => (
      <div key={i} className="bg-gray-800 rounded-lg p-4">
        <Skeleton className="h-6 w-3/4 mb-2" />
        <Skeleton className="h-4 w-full mb-1" />
        <Skeleton className="h-4 w-2/3" />
      </div>
    ))}
  </div>
);

export default LoadingSequence;

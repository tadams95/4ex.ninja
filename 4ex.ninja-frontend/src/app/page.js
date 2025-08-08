'use client';
import dynamic from 'next/dynamic';
import { Suspense } from 'react';
import { ConditionalMotionDiv } from '../components/ui';
import SubscribeButton from './components/SubscribeButton';

// Lazy load CurrencyTicker component (WebSocket + animation heavy)
const CurrencyTicker = dynamic(() => import('./components/CurrencyTicker'), {
  loading: () => (
    <div className="h-16 bg-neutral-900 border-b border-neutral-800 flex items-center justify-center">
      <div className="text-sm text-neutral-400">Loading market data...</div>
    </div>
  ),
  ssr: false, // Disable SSR for WebSocket component
});

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-black text-white">
      <Suspense
        fallback={
          <div className="h-16 bg-neutral-900 border-b border-neutral-800 flex items-center justify-center">
            <div className="text-sm text-neutral-400">Loading market data...</div>
          </div>
        }
      >
        <CurrencyTicker />
      </Suspense>
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="container mx-auto max-w-2xl text-center">
          <ConditionalMotionDiv
            motionProps={{
              initial: { opacity: 0, y: 20 },
              animate: { opacity: 1, y: 0 },
              transition: { duration: 0.8 },
            }}
            fallbackClassName="animate-fade-in"
          >
            <ConditionalMotionDiv
              motionProps={{
                whileHover: { scale: 1.05 },
              }}
              fallbackClassName=""
              className="text-4xl font-bold mb-6"
            >
              Welcome to 4ex.ninja
            </ConditionalMotionDiv>
            <ConditionalMotionDiv
              motionProps={{
                initial: { opacity: 0 },
                animate: { opacity: 1 },
                transition: { duration: 0.8, delay: 0.3 },
              }}
              fallbackClassName="animate-fade-in"
              className="mb-4 text-lg"
            >
              Get access to premium forex signals and boost your trading strategy.
            </ConditionalMotionDiv>
            <ConditionalMotionDiv
              motionProps={{
                initial: { opacity: 0 },
                animate: { opacity: 1 },
                transition: { delay: 0.6 },
              }}
              fallbackClassName="animate-fade-in"
            >
              <SubscribeButton />
            </ConditionalMotionDiv>
          </ConditionalMotionDiv>
        </div>
      </div>
    </div>
  );
}

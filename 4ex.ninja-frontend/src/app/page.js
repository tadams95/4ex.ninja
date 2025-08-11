'use client';
import { WalletButton } from '@/components/WalletConnection';
import WelcomeBanner from '@/components/WelcomeBanner';
import dynamic from 'next/dynamic';
import { Suspense, useEffect, useState } from 'react';
import { useAccount } from 'wagmi';
import { ConditionalMotionDiv } from '../components/ui';

// Lazy load CurrencyTicker component (WebSocket + animation heavy)
const CurrencyTicker = dynamic(() => import('./components/CurrencyTicker'), {
  loading: () => (
    <div className="h-16 bg-black border-b border-black flex items-center justify-center">
      <div className="text-sm text-neutral-400">Loading market data...</div>
    </div>
  ),
  ssr: false, // Disable SSR for WebSocket component
});

export default function Home() {
  const { isConnected } = useAccount();
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-black text-white">
      <Suspense
        fallback={
          <div className="h-16 bg-black border-b border-black flex items-center justify-center">
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
            {/* Welcome Banner for Connected Users */}
            {isHydrated && isConnected && (
              <ConditionalMotionDiv
                motionProps={{
                  initial: { opacity: 0, y: -10 },
                  animate: { opacity: 1, y: 0 },
                  transition: { duration: 0.5 },
                }}
                fallbackClassName="animate-fade-in"
                className="mb-8"
              >
                <WelcomeBanner />
              </ConditionalMotionDiv>
            )}

            <ConditionalMotionDiv
              motionProps={{
                whileHover: { scale: 1.05 },
              }}
              fallbackClassName=""
              className="text-4xl font-bold mb-6"
            >
              Welcome to 4EX.NINJA
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
              {isHydrated && isConnected
                ? 'Your premium forex signals dashboard is ready. Start trading with confidence.'
                : 'Get access to the 4EX platform.'}
            </ConditionalMotionDiv>

            {/* Only show connect button if not connected */}
            {isHydrated && !isConnected && (
              <ConditionalMotionDiv
                motionProps={{
                  initial: { opacity: 0 },
                  animate: { opacity: 1 },
                  transition: { delay: 0.6 },
                }}
                fallbackClassName="animate-fade-in"
              >
                <WalletButton size="lg" variant="primary" />
              </ConditionalMotionDiv>
            )}
          </ConditionalMotionDiv>
        </div>
      </div>
    </div>
  );
}

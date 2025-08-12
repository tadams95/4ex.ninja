'use client';
import WelcomeBanner from '@/components/WelcomeBanner';
import { Avatar, Identity, Name } from '@coinbase/onchainkit/identity';
import {
  ConnectWallet,
  Wallet,
  WalletDropdown,
  WalletDropdownDisconnect,
  WalletDropdownLink,
} from '@coinbase/onchainkit/wallet';
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
                ? 'Your 4EX dashboard is ready. Approach the markets with confidence.'
                : 'Get access to the 4EX platform.'}
            </ConditionalMotionDiv>

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

            {/* Only show connect button if not connected */}
            {isHydrated && !isConnected && (
              <ConditionalMotionDiv
                motionProps={{
                  initial: { opacity: 0 },
                  animate: { opacity: 1 },
                  transition: { delay: 0.6 },
                }}
                fallbackClassName="animate-fade-in"
                className="flex justify-center"
              >
                <Wallet>
                  <ConnectWallet
                    className="bg-green-700 hover:bg-green-800 active:bg-green-900
                      text-white border border-green-600 hover:border-green-500 
                      hover:text-green-100 font-semibold rounded-xl 
                      transition-all duration-300 ease-out px-4 py-2.5 text-sm 
                      cursor-pointer outline-none hover:shadow-lg 
                      hover:shadow-green-500/25 hover:scale-[1.02] active:scale-[0.98]
                      focus-visible:ring-2 focus-visible:ring-green-500 
                      focus-visible:ring-offset-2 focus-visible:ring-offset-black
                      min-h-[44px] flex items-center justify-center"
                    aria-label="Connect your crypto wallet"
                  >
                    <Avatar className="h-6 w-6" aria-hidden="true" />
                    <Name aria-label="Wallet display name" />
                  </ConnectWallet>
                  <WalletDropdown>
                    <Identity
                      className="px-4 pt-3 pb-2 group hover:bg-neutral-800/50 
                        transition-colors duration-200 rounded-t-lg min-h-[44px] 
                        flex items-center focus-within:ring-2 focus-within:ring-green-500/50"
                      hasCopyAddressOnClick
                    >
                      <Avatar
                        className="ring-2 ring-green-500/20 group-hover:ring-green-500/40 
                        transition-all duration-200"
                        aria-hidden="true"
                      />
                      <Name
                        className="font-medium text-white group-hover:text-green-100"
                        aria-label="Connected wallet name"
                      />
                    </Identity>
                    <WalletDropdownLink
                      className="flex items-center px-4 py-3 hover:bg-neutral-800/50 
                        transition-all duration-200 group min-h-[44px] rounded-md mx-2 my-1
                        focus:outline-none focus:ring-2 focus:ring-green-500/50"
                      icon="wallet"
                      href="https://wallet.coinbase.com"
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label="Open Coinbase Wallet in new tab"
                    >
                      Open Wallet
                    </WalletDropdownLink>
                    <WalletDropdownLink
                      className="flex items-center px-4 py-3 hover:bg-neutral-800/50 
                        transition-all duration-200 group min-h-[44px] rounded-md mx-2 my-1
                        focus:outline-none focus:ring-2 focus:ring-green-500/50"
                      icon="user"
                      href="/account"
                      aria-label="Go to account settings"
                    >
                      Account Settings
                    </WalletDropdownLink>
                    <WalletDropdownDisconnect
                      className="mx-2 my-1 hover:bg-red-500/10 hover:text-red-300 
                        transition-all duration-200 min-h-[44px] rounded-md
                        focus:outline-none focus:ring-2 focus:ring-red-500/50"
                      aria-label="Disconnect wallet"
                    />
                  </WalletDropdown>
                </Wallet>
              </ConditionalMotionDiv>
            )}
          </ConditionalMotionDiv>
        </div>
      </div>
    </div>
  );
}

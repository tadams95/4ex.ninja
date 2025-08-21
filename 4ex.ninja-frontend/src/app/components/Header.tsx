'use client';
import { HeaderErrorBoundary } from '@/components/error';
import { Avatar, Identity, Name } from '@coinbase/onchainkit/identity';
import {
  ConnectWallet,
  Wallet,
  WalletDropdown,
  WalletDropdownDisconnect,
  WalletDropdownLink,
} from '@coinbase/onchainkit/wallet';
import Link from 'next/link';
import { memo, useCallback, useEffect, useState } from 'react';
import { useAccount } from 'wagmi';

const HeaderComponent = memo(function HeaderComponent() {
  const [isMenuOpen, setIsMenuOpen] = useState<boolean>(false);
  const [isMobile, setIsMobile] = useState<boolean>(false);
  const [isHydrated, setIsHydrated] = useState<boolean>(false);
  const { isConnected } = useAccount();

  // Handle hydration
  useEffect(() => {
    setIsHydrated(true);
  }, []);

  // Check screen size on component mount and resize
  useEffect(() => {
    const checkScreenSize = (): void => {
      setIsMobile(window.innerWidth < 768);
    };

    // Initial check
    checkScreenSize();

    // Add event listener
    window.addEventListener('resize', checkScreenSize);

    // Clean up
    return () => window.removeEventListener('resize', checkScreenSize);
  }, []);

  const toggleMenu = useCallback((): void => {
    setIsMenuOpen(!isMenuOpen);
  }, [isMenuOpen]);

  const handleNavClick = useCallback(() => {
    if (isMobile) setIsMenuOpen(false);
  }, [isMobile]);

  return (
    <header className="bg-black text-white py-6">
      <div className="container mx-auto flex justify-between items-center px-4 md:px-6 lg:px-8">
        <Link href="/" className="text-2xl font-bold">
          4ex.ninja
        </Link>

        {/* Hamburger Icon - enhanced for touch accessibility */}
        <button
          className="md:hidden flex flex-col justify-center items-center
            min-h-[44px] min-w-[44px] p-2 rounded-lg hover:bg-neutral-800/50
            transition-all duration-200 focus:outline-none focus:ring-2 
            focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-black
            active:bg-neutral-700/50"
          onClick={toggleMenu}
          aria-label="Toggle navigation menu"
          aria-expanded={isMenuOpen}
        >
          <span
            className={`block w-6 h-0.5 bg-white mb-1.5 transition-all duration-300 ${
              isMenuOpen ? 'rotate-45 translate-y-2' : ''
            }`}
          ></span>
          <span
            className={`block w-6 h-0.5 bg-white mb-1.5 transition-all duration-300 ${
              isMenuOpen ? 'opacity-0' : 'opacity-100'
            }`}
          ></span>
          <span
            className={`block w-6 h-0.5 bg-white transition-all duration-300 ${
              isMenuOpen ? '-rotate-45 -translate-y-2' : ''
            }`}
          ></span>
        </button>

        {/* Navigation - full size on desktop, expandable on mobile */}
        <nav className={`${isMobile ? (isMenuOpen ? 'block' : 'hidden') : 'block'} md:block`}>
          <ul
            className={`
            ${
              isMobile
                ? 'flex flex-col absolute right-0 top-16 bg-black p-6 w-48 shadow-lg z-50'
                : 'flex space-x-6 items-center'
            } 
            md:flex md:items-center md:space-x-6 md:static md:shadow-none md:p-0 md:w-auto
          `}
          >
            {/* Navigation Links - enhanced for touch */}
            <li className="py-3 md:py-0">
              <Link
                href="/about"
                prefetch={true}
                onClick={handleNavClick}
                className="hover:text-green-500 transition-colors duration-200
                  focus:outline-none focus:text-green-400 focus:ring-2 
                  focus:ring-green-500/50 rounded-md px-2 py-1 min-h-[44px] 
                  flex items-center"
                aria-label="About page"
              >
                About
              </Link>
            </li>
            <li className="py-3 md:py-0">
              <Link
                href="/insights"
                prefetch={true}
                onClick={handleNavClick}
                className="hover:text-green-500 transition-colors duration-200
                  focus:outline-none focus:text-green-400 focus:ring-2 
                  focus:ring-green-500/50 rounded-md px-2 py-1 min-h-[44px] 
                  flex items-center"
                aria-label="Insights"
              >
                Insights
              </Link>
            </li>

            <li className="py-3 md:py-0">
              <Link
                href="/swap"
                prefetch={true}
                onClick={handleNavClick}
                className="hover:text-green-500 transition-colors duration-200
                  focus:outline-none focus:text-green-400 focus:ring-2 
                  focus:ring-green-500/50 rounded-md px-2 py-1 min-h-[44px] 
                  flex items-center"
                aria-label="Buy $4EX tokens"
              >
                Swap
              </Link>
            </li>

            {!isHydrated ? (
              // Enhanced hydration placeholder with better skeleton
              <li className="py-3 md:py-0">
                <div
                  className="bg-gradient-to-r from-neutral-800 via-neutral-700 to-neutral-800 
                  animate-shimmer rounded-xl px-4 py-2.5 w-32 h-10 
                  bg-[length:200%_100%] flex items-center justify-center
                  border border-neutral-700"
                >
                  <div className="w-5 h-5 bg-neutral-600 rounded-full mr-2 animate-pulse"></div>
                  <div className="w-16 h-3 bg-neutral-600 rounded animate-pulse"></div>
                </div>
              </li>
            ) : (
              <li className="py-3 md:py-0">
                <Wallet>
                  <ConnectWallet
                    className="bg-green-700 hover:bg-green-800 active:bg-green-900
                      text-white border border-green-600 hover:border-green-500 
                      hover:text-green-100 font-semibold 
                      rounded-xl transition-all duration-300 ease-out 
                      px-4 py-2.5 text-sm cursor-pointer outline-none 
                      hover:shadow-lg hover:shadow-green-500/25 hover:scale-[1.02] 
                      active:scale-[0.98] focus-visible:ring-2 focus-visible:ring-green-500 
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
              </li>
            )}
          </ul>
        </nav>
      </div>
    </header>
  );
});

export default function Header() {
  return (
    <HeaderErrorBoundary>
      <HeaderComponent />
    </HeaderErrorBoundary>
  );
}

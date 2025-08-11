'use client';
import { HeaderErrorBoundary } from '@/components/error';
import { WalletButton, WalletProfile } from '@/components/WalletConnection';
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
    <header className="bg-black text-white pt-4 pb-4">
      <div className="container mx-auto flex justify-between items-center px-4">
        <Link href="/" className="text-2xl font-bold">
          4ex.ninja
        </Link>

        {/* Hamburger Icon - only visible on mobile */}
        <button
          className="md:hidden flex flex-col justify-center items-center"
          onClick={toggleMenu}
          aria-label="Toggle navigation menu"
        >
          <span
            className={`block w-6 h-0.5 bg-white mb-1.5 transition-all ${
              isMenuOpen ? 'rotate-45 translate-y-2' : ''
            }`}
          ></span>
          <span
            className={`block w-6 h-0.5 bg-white mb-1.5 transition-all ${
              isMenuOpen ? 'opacity-0' : 'opacity-100'
            }`}
          ></span>
          <span
            className={`block w-6 h-0.5 bg-white transition-all ${
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
                ? 'flex flex-col absolute right-0 top-16 bg-black p-4 w-48 shadow-lg z-50'
                : 'flex space-x-4 items-center'
            } 
            md:flex md:items-center md:space-x-4 md:static md:shadow-none md:p-0 md:w-auto
          `}
          >
            {/* Navigation Links */}
            <li className="py-2 md:py-0">
              <Link
                href="/"
                onClick={handleNavClick}
                className="hover:text-green-400 transition-colors"
              >
                Home
              </Link>
            </li>
            <li className="py-2 md:py-0">
              <Link
                href="/about"
                onClick={handleNavClick}
                className="hover:text-green-400 transition-colors"
              >
                About
              </Link>
            </li>
            <li className="py-2 md:py-0">
              <Link
                href="/feed"
                onClick={handleNavClick}
                className="hover:text-green-400 transition-colors"
              >
                Signals
              </Link>
            </li>

            {/* Wallet Connection */}
            {!isHydrated ? (
              // Hydration placeholder
              <li className="py-2 md:py-0">
                <div className="bg-gray-700 animate-pulse rounded-lg px-4 py-2 w-32 h-8"></div>
              </li>
            ) : (
              <>
                {/* Show Account link when connected */}
                {isConnected && (
                  <li className="py-2 md:py-0">
                    <Link
                      href="/account"
                      onClick={handleNavClick}
                      className="text-green-400 hover:text-green-300 transition-colors font-medium"
                    >
                      Account
                    </Link>
                  </li>
                )}

                {/* Show Connect button when disconnected, Profile when connected */}
                <li className="py-2 md:py-0">
                  {isConnected ? (
                    <WalletProfile size="sm" />
                  ) : (
                    <WalletButton size="sm" variant="outline" />
                  )}
                </li>
              </>
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

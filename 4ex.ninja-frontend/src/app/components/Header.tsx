'use client';
import { HeaderErrorBoundary } from '@/components/error';
import WalletConnectionOnchain from '@/components/WalletConnectionOnchain';
import { signOut, useSession } from 'next-auth/react';
import Link from 'next/link';
import { memo, useCallback, useEffect, useState } from 'react';

const HeaderComponent = memo(function HeaderComponent() {
  const { data: session, status } = useSession();
  const [isMenuOpen, setIsMenuOpen] = useState<boolean>(false);
  const [isMobile, setIsMobile] = useState<boolean>(false);

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

  const handleSignOut = useCallback(() => {
    signOut({ callbackUrl: '/' });
    if (isMobile) setIsMenuOpen(false);
  }, [isMobile]);

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
            <li className="py-2 md:py-0">
              <Link href="/" onClick={handleNavClick}>
                Home
              </Link>
            </li>
            <li className="py-2 md:py-0">
              <Link href="/about" onClick={handleNavClick}>
                About
              </Link>
            </li>
            {/* Only show feed link if authenticated */}
            {status === 'authenticated' && (
              <li className="py-2 md:py-0">
                <Link href="/feed" onClick={handleNavClick}>
                  Signals
                </Link>
              </li>
            )}

            {/* Authentication links */}
            {status === 'authenticated' ? (
              <>
                <li className="py-2 md:py-0">
                  <Link href="/account" onClick={handleNavClick} className="text-green-500">
                    Account
                  </Link>
                </li>
                <li className="py-2 md:py-0">
                  <button
                    onClick={handleSignOut}
                    className="text-red-500"
                    data-testid="sign-out-button"
                  >
                    Sign Out
                  </button>
                </li>
              </>
            ) : (
              <>
                <li className="py-2 md:py-0">
                  <Link
                    href="/login"
                    onClick={handleNavClick}
                    className="bg-green-700 hover:bg-green-800 px-4 py-1 rounded"
                  >
                    Log in
                  </Link>
                </li>
              </>
            )}

            {/* Wallet Connection - Always visible */}
            <li className="py-2 md:py-0">
              <WalletConnectionOnchain />
            </li>
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

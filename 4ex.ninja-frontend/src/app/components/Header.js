"use client";
import Link from "next/link";
import { useState, useEffect } from "react";
import { useSession, signOut } from "next-auth/react";

export default function Header() {
  const { data: session, status } = useSession();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  
  // Check screen size on component mount and resize
  useEffect(() => {
    const checkScreenSize = () => {
      setIsMobile(window.innerWidth < 768);
    };

    // Initial check
    checkScreenSize();

    // Add event listener
    window.addEventListener("resize", checkScreenSize);

    // Clean up
    return () => window.removeEventListener("resize", checkScreenSize);
  }, []);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

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
              isMenuOpen ? "rotate-45 translate-y-2" : ""
            }`}
          ></span>
          <span
            className={`block w-6 h-0.5 bg-white mb-1.5 transition-all ${
              isMenuOpen ? "opacity-0" : "opacity-100"
            }`}
          ></span>
          <span
            className={`block w-6 h-0.5 bg-white transition-all ${
              isMenuOpen ? "-rotate-45 -translate-y-2" : ""
            }`}
          ></span>
        </button>

        {/* Navigation - full size on desktop, expandable on mobile */}
        <nav
          className={`${
            isMobile ? (isMenuOpen ? "block" : "hidden") : "block"
          } md:block`}
        >
          <ul
            className={`
            ${
              isMobile
                ? "flex flex-col absolute right-0 top-16 bg-black p-4 w-48 shadow-lg z-50"
                : "flex space-x-4 items-center"
            } 
            md:flex md:items-center md:space-x-4 md:static md:shadow-none md:p-0 md:w-auto
          `}
          >
            <li className="py-2 md:py-0">
              <Link href="/" onClick={() => isMobile && setIsMenuOpen(false)}>
                Home
              </Link>
            </li>
            <li className="py-2 md:py-0">
              <Link
                href="/about"
                onClick={() => isMobile && setIsMenuOpen(false)}
              >
                About
              </Link>
            </li>
            {/* Only show feed link if authenticated */}
            {status === "authenticated" && (
              <li className="py-2 md:py-0">
                <Link
                  href="/feed"
                  onClick={() => isMobile && setIsMenuOpen(false)}
                >
                  Signals
                </Link>
              </li>
            )}
            
            {/* Authentication links */}
            {status === "authenticated" ? (
              <>
                <li className="py-2 md:py-0">
                  <Link
                    href="/account"
                    onClick={() => isMobile && setIsMenuOpen(false)}
                    className="text-green-500"
                  >
                    Account
                  </Link>
                </li>
                <li className="py-2 md:py-0">
                  <button
                    onClick={() => {
                      signOut({ callbackUrl: '/' });
                      isMobile && setIsMenuOpen(false);
                    }}
                    className="text-red-500"
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
                    onClick={() => isMobile && setIsMenuOpen(false)}
                    className="bg-green-700 hover:bg-green-800 px-4 py-1 rounded"
                  >
                    Log in
                  </Link>
                </li>
              </>
            )}
          </ul>
        </nav>
      </div>
    </header>
  );
}

"use client";
import Link from "next/link";
import { useState, useEffect } from "react";

export default function Header() {
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
                : "flex space-x-4"
            } 
            md:flex md:space-x-4 md:static md:shadow-none md:p-0 md:w-auto
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
            <li className="py-2 md:py-0">
              <Link
                href="/feed"
                onClick={() => isMobile && setIsMenuOpen(false)}
              >
                Feed
              </Link>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
}

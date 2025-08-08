'use client';

import { useEffect, useState } from 'react';

export const useFramerMotion = () => {
  const [motion, setMotion] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadMotion = async () => {
      try {
        const framerMotion = await import('framer-motion');
        setMotion(framerMotion);
      } catch (error) {
        console.error('Failed to load framer-motion:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadMotion();
  }, []);

  return { motion, isLoading };
};

// Hook for prefers-reduced-motion
export const usePrefersReducedMotion = () => {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (event: MediaQueryListEvent) => {
      setPrefersReducedMotion(event.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return prefersReducedMotion;
};

'use client';

/**
 * Animation utilities for conditional loading of framer-motion animations
 * This helps reduce the initial bundle size by only loading animations when needed
 */

import { useEffect, useState } from 'react';

// Simple types for the most common motion properties we use
export interface BasicMotionProps {
  initial?: any;
  animate?: any;
  transition?: any;
  whileHover?: any;
  whileTap?: any;
  [key: string]: any;
}

// Hook to check if user prefers reduced motion
export const usePrefersReducedMotion = (): boolean => {
  const [prefersReduced, setPrefersReduced] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReduced(mediaQuery.matches);

    const handleChange = (event: MediaQueryListEvent) => {
      setPrefersReduced(event.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return prefersReduced;
};

// Hook to conditionally load framer-motion only when animations are needed
export const useConditionalMotion = () => {
  const [motionComponents, setMotionComponents] = useState<any>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const prefersReduced = usePrefersReducedMotion();

  const loadMotion = async () => {
    if (prefersReduced || isLoaded) return;

    try {
      const { motion, AnimatePresence } = await import('framer-motion');
      setMotionComponents({ motion, AnimatePresence });
      setIsLoaded(true);
    } catch (error) {
      console.error('Failed to load framer-motion:', error);
    }
  };

  return {
    motion: motionComponents?.motion,
    AnimatePresence: motionComponents?.AnimatePresence,
    isLoaded,
    prefersReduced,
    loadMotion,
  };
};

// Utility to create CSS-only fallback animations
export const createCSSFallback = (animationType: 'fadeIn' | 'slideUp' | 'scale' = 'fadeIn') => {
  const animations = {
    fadeIn: 'animate-fade-in',
    slideUp: 'animate-slide-up',
    scale: 'animate-scale-in',
  };

  return animations[animationType] || animations.fadeIn;
};

'use client';

/**
 * Animation utilities for conditional loading of framer-motion animations
 * This helps reduce the initial bundle size by only loading animations when needed
 * Includes mobile-specific optimizations and hardware acceleration
 */

import { useEffect, useState } from 'react';

// Simple types for the most common motion properties we use
export interface BasicMotionProps {
  initial?: any;
  animate?: any;
  transition?: any;
  whileHover?: any;
  whileTap?: any;
  whileInView?: any;
  viewport?: any;
  [key: string]: any;
}

// Hook to detect device capabilities for animation optimization
export const useDeviceCapabilities = () => {
  const [capabilities, setCapabilities] = useState({
    isMobile: false,
    isLowEnd: false,
    supportsHardwareAcceleration: true,
    prefersReducedMotion: false,
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
      navigator.userAgent
    );
    const isLowEnd = navigator.hardwareConcurrency ? navigator.hardwareConcurrency <= 2 : false;
    const supportsHardwareAcceleration = 'transform3d' in document.documentElement.style;

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const prefersReducedMotion = mediaQuery.matches;

    setCapabilities({
      isMobile,
      isLowEnd,
      supportsHardwareAcceleration,
      prefersReducedMotion,
    });

    const handleChange = (event: MediaQueryListEvent) => {
      setCapabilities(prev => ({
        ...prev,
        prefersReducedMotion: event.matches,
      }));
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return capabilities;
};

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
  const { isMobile, isLowEnd } = useDeviceCapabilities();

  const loadMotion = async () => {
    if (prefersReduced || isLoaded) return;

    try {
      // Load framer-motion components
      const { motion, AnimatePresence } = await import('framer-motion');

      // For low-end devices, we'll just use motion directly but apply optimizations at the component level
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
    isMobile,
    isLowEnd,
    loadMotion,
  };
};

// Utility to create optimized animation configurations based on device
export const createOptimizedAnimation = (
  animationType:
    | 'fadeIn'
    | 'slideUp'
    | 'slideDown'
    | 'slideLeft'
    | 'slideRight'
    | 'scale' = 'fadeIn',
  deviceCapabilities?: ReturnType<typeof useDeviceCapabilities>
) => {
  const isMobile = deviceCapabilities?.isMobile || false;
  const isLowEnd = deviceCapabilities?.isLowEnd || false;
  const prefersReduced = deviceCapabilities?.prefersReducedMotion || false;

  // For reduced motion or low-end devices, return static styles
  if (prefersReduced || isLowEnd) {
    return {
      cssClass: '',
      motionProps: {},
    };
  }

  const animations = {
    fadeIn: {
      cssClass: 'animate-fade-in',
      motionProps: {
        initial: { opacity: 0 },
        animate: { opacity: 1 },
        transition: { duration: isMobile ? 0.2 : 0.3 },
      },
    },
    slideUp: {
      cssClass: 'animate-slide-up',
      motionProps: {
        initial: { opacity: 0, y: isMobile ? 10 : 20 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: isMobile ? 0.2 : 0.3 },
      },
    },
    slideDown: {
      cssClass: 'animate-slide-down',
      motionProps: {
        initial: { opacity: 0, y: isMobile ? -10 : -20 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: isMobile ? 0.2 : 0.3 },
      },
    },
    slideLeft: {
      cssClass: 'animate-slide-left',
      motionProps: {
        initial: { opacity: 0, x: isMobile ? 10 : 20 },
        animate: { opacity: 1, x: 0 },
        transition: { duration: isMobile ? 0.2 : 0.3 },
      },
    },
    slideRight: {
      cssClass: 'animate-slide-right',
      motionProps: {
        initial: { opacity: 0, x: isMobile ? -10 : -20 },
        animate: { opacity: 1, x: 0 },
        transition: { duration: isMobile ? 0.2 : 0.3 },
      },
    },
    scale: {
      cssClass: 'animate-scale-in',
      motionProps: {
        initial: { opacity: 0, scale: 0.95 },
        animate: { opacity: 1, scale: 1 },
        transition: { duration: isMobile ? 0.2 : 0.3 },
      },
    },
  };

  return animations[animationType] || animations.fadeIn;
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

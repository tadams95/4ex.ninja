'use client';

import { useConditionalMotion } from '@/utils/animation';
import React, { useCallback, useMemo } from 'react';

interface OptimizedMotionProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  enableMotion?: boolean;
  motionProps?: {
    initial?: any;
    animate?: any;
    transition?: any;
    whileHover?: any;
    whileTap?: any;
    whileInView?: any;
    viewport?: any;
  };
  fallbackClassName?: string;
  /**
   * Animation complexity level
   * 'simple' - Use CSS transitions/transforms for better performance
   * 'complex' - Use framer-motion for advanced animations
   * 'auto' - Automatically choose based on motion props complexity
   */
  complexity?: 'simple' | 'complex' | 'auto';
  /**
   * Force hardware acceleration
   */
  forceGPU?: boolean;
}

/**
 * Intelligently chooses between CSS and framer-motion based on animation complexity
 * This provides optimal performance by using CSS for simple animations and framer-motion for complex ones
 */
export const OptimizedMotion: React.FC<OptimizedMotionProps> = ({
  children,
  enableMotion = true,
  motionProps = {},
  fallbackClassName = 'animate-fade-in',
  complexity = 'auto',
  forceGPU = true,
  className = '',
  ...divProps
}) => {
  const { motion, isLoaded, prefersReduced, loadMotion } = useConditionalMotion();

  // Analyze motion complexity to determine if we need framer-motion
  const isComplexAnimation = useMemo(() => {
    if (complexity === 'simple') return false;
    if (complexity === 'complex') return true;

    // Auto-detect complexity
    const hasComplexProps = !!(
      motionProps.whileInView ||
      motionProps.viewport ||
      (motionProps.transition && typeof motionProps.transition === 'object') ||
      (motionProps.animate &&
        typeof motionProps.animate === 'object' &&
        Object.keys(motionProps.animate).some(
          key => !['x', 'y', 'scale', 'opacity', 'rotate'].includes(key)
        ))
    );

    return hasComplexProps;
  }, [motionProps, complexity]);

  // Generate CSS-based animation classes for simple animations
  const generateCSSClasses = useCallback(() => {
    const classes = [];

    if (forceGPU) {
      classes.push('gpu-accelerated');
    }

    // Simple hover effects using CSS
    if (motionProps.whileHover) {
      const { scale, x, y, opacity } = motionProps.whileHover;
      if (scale && scale > 1) {
        classes.push('hover:scale-105');
      } else if (scale && scale < 1) {
        classes.push('hover:scale-95');
      }
      if (x || y) {
        classes.push('hover:translate-x-1', 'hover:translate-y-1');
      }
      if (opacity !== undefined) {
        classes.push('hover:opacity-80');
      }
      classes.push('transition-transform duration-200 will-change-transform');
    }

    // Simple tap effects using CSS
    if (motionProps.whileTap) {
      const { scale } = motionProps.whileTap;
      if (scale && scale < 1) {
        classes.push('active:scale-95');
      }
    }

    return classes.join(' ');
  }, [motionProps, forceGPU]);

  // If motion is disabled or user prefers reduced motion, use static div
  if (!enableMotion || prefersReduced) {
    return (
      <div className={className} {...divProps}>
        {children}
      </div>
    );
  }

  // For simple animations, use CSS for better performance
  if (!isComplexAnimation) {
    const cssClasses = generateCSSClasses();
    return (
      <div className={`${className} ${fallbackClassName} ${cssClasses}`} {...divProps}>
        {children}
      </div>
    );
  }

  // For complex animations, load framer-motion
  React.useEffect(() => {
    if (isComplexAnimation) {
      loadMotion();
    }
  }, [isComplexAnimation, loadMotion]);

  // If motion is not yet loaded for complex animations, use CSS fallback
  if (!isLoaded || !motion) {
    return (
      <div className={`${className} ${fallbackClassName}`} {...divProps}>
        {children}
      </div>
    );
  }

  // Use framer-motion for complex animations
  const MotionDiv = motion.div;
  return (
    <MotionDiv className={className} {...motionProps} {...divProps}>
      {children}
    </MotionDiv>
  );
};

export default OptimizedMotion;

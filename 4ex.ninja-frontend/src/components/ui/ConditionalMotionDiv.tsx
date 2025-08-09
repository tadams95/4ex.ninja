'use client';

import { useConditionalMotion } from '@/utils/animation';
import React, { useEffect, useState } from 'react';

interface ConditionalMotionDivProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  enableMotion?: boolean;
  motionProps?: {
    initial?: any;
    animate?: any;
    transition?: any;
    whileHover?: any;
    whileTap?: any;
  };
  fallbackClassName?: string;
  /**
   * Force GPU acceleration for better performance
   */
  forceGPU?: boolean;
}

/**
 * A div that conditionally uses framer-motion or falls back to CSS animations
 * This helps reduce bundle size by only loading framer-motion when needed
 * Includes mobile optimizations and hardware acceleration
 */
export const ConditionalMotionDiv: React.FC<ConditionalMotionDivProps> = ({
  children,
  enableMotion = true,
  motionProps = {},
  fallbackClassName = 'animate-fade-in',
  forceGPU = true,
  className = '',
  ...divProps
}) => {
  const { motion, isLoaded, prefersReduced, isMobile, isLowEnd, loadMotion } =
    useConditionalMotion();
  const [shouldAnimate, setShouldAnimate] = useState(false);

  useEffect(() => {
    if (enableMotion && !prefersReduced) {
      setShouldAnimate(true);
      loadMotion();
    }
  }, [enableMotion, prefersReduced, loadMotion]);

  // Enhanced class generation with mobile optimizations
  const generateOptimizedClasses = () => {
    const classes = [className];

    if (forceGPU && !prefersReduced) {
      classes.push('gpu-accelerated');
    }

    // Reduce animation complexity on low-end devices
    if (isLowEnd || (isMobile && !prefersReduced)) {
      classes.push('will-change-auto');
    } else if (!prefersReduced) {
      classes.push('will-change-transform');
    }

    return classes.join(' ');
  };

  const optimizedClasses = generateOptimizedClasses();

  // If motion is disabled or user prefers reduced motion, use static div
  if (!enableMotion || prefersReduced) {
    return (
      <div className={optimizedClasses} {...divProps}>
        {children}
      </div>
    );
  }

  // If motion is not yet loaded or loading, use CSS fallback
  if (!isLoaded || !motion) {
    return (
      <div className={`${optimizedClasses} ${fallbackClassName}`} {...divProps}>
        {children}
      </div>
    );
  }

  // Optimize motion props for mobile devices
  const optimizedMotionProps = { ...motionProps };
  if (isMobile || isLowEnd) {
    // Reduce animation duration and complexity for mobile
    if (optimizedMotionProps.transition) {
      optimizedMotionProps.transition = {
        ...optimizedMotionProps.transition,
        duration: Math.min(optimizedMotionProps.transition.duration || 0.3, 0.2),
      };
    } else {
      optimizedMotionProps.transition = { duration: 0.2, ease: 'easeOut' };
    }
  }

  // Use framer-motion when available
  const MotionDiv = motion.div;
  return (
    <MotionDiv className={optimizedClasses} {...optimizedMotionProps} {...divProps}>
      {children}
    </MotionDiv>
  );
};

export default ConditionalMotionDiv;

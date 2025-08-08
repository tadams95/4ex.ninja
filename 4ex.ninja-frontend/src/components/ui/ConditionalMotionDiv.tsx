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
}

/**
 * A div that conditionally uses framer-motion or falls back to CSS animations
 * This helps reduce bundle size by only loading framer-motion when needed
 */
export const ConditionalMotionDiv: React.FC<ConditionalMotionDivProps> = ({
  children,
  enableMotion = true,
  motionProps = {},
  fallbackClassName = 'animate-fade-in',
  className = '',
  ...divProps
}) => {
  const { motion, isLoaded, prefersReduced, loadMotion } = useConditionalMotion();
  const [shouldAnimate, setShouldAnimate] = useState(false);

  useEffect(() => {
    if (enableMotion && !prefersReduced) {
      setShouldAnimate(true);
      loadMotion();
    }
  }, [enableMotion, prefersReduced, loadMotion]);

  // If motion is disabled or user prefers reduced motion, use static div
  if (!enableMotion || prefersReduced) {
    return (
      <div className={className} {...divProps}>
        {children}
      </div>
    );
  }

  // If motion is not yet loaded or loading, use CSS fallback
  if (!isLoaded || !motion) {
    return (
      <div className={`${className} ${fallbackClassName}`} {...divProps}>
        {children}
      </div>
    );
  }

  // Use framer-motion when available
  const MotionDiv = motion.div;
  return (
    <MotionDiv className={className} {...motionProps} {...divProps}>
      {children}
    </MotionDiv>
  );
};

export default ConditionalMotionDiv;

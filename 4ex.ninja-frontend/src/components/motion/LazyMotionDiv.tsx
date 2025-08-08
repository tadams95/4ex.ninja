'use client';

import { motion, MotionProps } from 'framer-motion';
import dynamic from 'next/dynamic';
import { ComponentPropsWithRef, forwardRef } from 'react';

// Types for the motion div component
type MotionDivProps = ComponentPropsWithRef<'div'> & MotionProps;

// Static div fallback component when motion is not needed
const StaticDiv = forwardRef<HTMLDivElement, ComponentPropsWithRef<'div'>>(
  ({ children, ...props }, ref) => (
    <div ref={ref} {...props}>
      {children}
    </div>
  )
);
StaticDiv.displayName = 'StaticDiv';

// The actual motion component
const MotionDiv = forwardRef<HTMLDivElement, MotionDivProps>(({ children, ...props }, ref) => (
  <motion.div ref={ref} {...props}>
    {children}
  </motion.div>
));
MotionDiv.displayName = 'MotionDiv';

// Lazy-loaded motion div with fallback
const LazyMotionDiv = dynamic(() => Promise.resolve(MotionDiv), {
  ssr: false,
  loading: () => null, // No loading state, just render static div
});

// Props interface for the component
interface LazyMotionDivProps extends MotionDivProps {
  enableMotion?: boolean;
}

// Main component that conditionally renders motion
export const LazyMotionDiv = forwardRef<HTMLDivElement, LazyMotionDivProps>(
  ({ enableMotion = true, children, ...props }, ref) => {
    // If motion is disabled or we're in a server environment, use static div
    if (!enableMotion || typeof window === 'undefined') {
      return (
        <StaticDiv ref={ref} {...(props as ComponentPropsWithRef<'div'>)}>
          {children}
        </StaticDiv>
      );
    }

    // Use lazy-loaded motion div
    return (
      <LazyMotionDiv ref={ref} {...props}>
        {children}
      </LazyMotionDiv>
    );
  }
);

LazyMotionDiv.displayName = 'LazyMotionDiv';

export default LazyMotionDiv;

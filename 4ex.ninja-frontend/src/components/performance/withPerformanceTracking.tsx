/**
 * Performance Tracking Higher-Order Component
 *
 * Automatically adds performance monitoring to components for 1.10.6.3
 */

import { useAnimationPerformance } from '@/hooks/useAnimationPerformance';
import {
  usePageInteractionTracking,
  useRenderPerformance,
  useTradingFlowTracking,
} from '@/hooks/usePerformance';
import React, { useEffect, useRef } from 'react';

interface WithPerformanceTrackingProps {
  trackRender?: boolean;
  trackInteractions?: boolean;
  trackAnimations?: boolean;
  componentName?: string;
  performanceConfig?: {
    animationName?: string;
    tradingFlow?: string;
  };
}

/**
 * HOC that adds performance tracking to any component
 */
export function withPerformanceTracking<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  options: WithPerformanceTrackingProps = {}
) {
  const {
    trackRender = true,
    trackInteractions = true,
    trackAnimations = false,
    componentName = WrappedComponent.displayName || WrappedComponent.name || 'Unknown',
    performanceConfig = {},
  } = options;

  const PerformanceTrackedComponent = (props: P) => {
    const elementRef = useRef<HTMLDivElement>(null);

    // Track component render performance
    if (trackRender) {
      useRenderPerformance(componentName);
    }

    // Track page interactions
    const trackPageInteraction = usePageInteractionTracking();

    // Track trading flow interactions
    const trackTradingInteraction = useTradingFlowTracking();

    // Track animation performance if enabled
    const animationTracking = useAnimationPerformance(
      performanceConfig.animationName || `${componentName}_animation`,
      trackAnimations
    );

    // Add click tracking to the wrapper
    const handleClick = (event: React.MouseEvent) => {
      if (trackInteractions) {
        const finishTracking = trackPageInteraction(`${componentName}_click`);
        // Finish tracking after a short delay to capture paint time
        setTimeout(finishTracking, 16); // One frame at 60fps
      }

      // If it's a trading flow, track that too
      if (performanceConfig.tradingFlow) {
        const finishTradingTracking = trackTradingInteraction(
          performanceConfig.tradingFlow,
          'click'
        );
        setTimeout(finishTradingTracking, 16);
      }

      // Call original onClick if it exists
      if ('onClick' in props && typeof props.onClick === 'function') {
        (props.onClick as (event: React.MouseEvent) => void)(event);
      }
    };

    // Enhanced props with performance tracking
    const enhancedProps = {
      ...props,
      onClick: handleClick,
    } as P;

    return (
      <div ref={elementRef} data-performance-component={componentName}>
        <WrappedComponent {...enhancedProps} />
      </div>
    );
  };

  PerformanceTrackedComponent.displayName = `withPerformanceTracking(${componentName})`;

  return PerformanceTrackedComponent;
}

/**
 * Hook to automatically track performance for subscription flows
 */
export function useSubscriptionFlowTracking(flowStep: string) {
  const stepStartTime = useRef<number | null>(null);

  useEffect(() => {
    stepStartTime.current = performance.now();

    return () => {
      if (stepStartTime.current) {
        const duration = performance.now() - stepStartTime.current;

        // Import performance function dynamically to avoid circular deps
        import('@/utils/performance').then(({ recordSubscriptionStepCompletion }) => {
          recordSubscriptionStepCompletion(flowStep, stepStartTime.current!, 'automatic');
        });
      }
    };
  }, [flowStep]);

  const markStepComplete = (userAction?: string) => {
    if (stepStartTime.current) {
      import('@/utils/performance').then(({ recordSubscriptionStepCompletion }) => {
        recordSubscriptionStepCompletion(flowStep, stepStartTime.current!, userAction);
      });
      stepStartTime.current = performance.now(); // Reset for next step
    }
  };

  return { markStepComplete };
}

/**
 * Component wrapper for subscription flow pages
 */
export function SubscriptionFlowWrapper({
  children,
  flowStep,
  className = '',
}: {
  children: React.ReactNode;
  flowStep: string;
  className?: string;
}) {
  const { markStepComplete } = useSubscriptionFlowTracking(flowStep);

  return (
    <div
      className={`subscription-flow-step ${className}`}
      data-flow-step={flowStep}
      onTransitionEnd={() => markStepComplete('transition_complete')}
    >
      {children}
    </div>
  );
}

/**
 * Performance tracking for trading components
 */
export function TradingComponentWrapper({
  children,
  flowType,
  className = '',
}: {
  children: React.ReactNode;
  flowType: string;
  className?: string;
}) {
  const trackTradingInteraction = useTradingFlowTracking();

  const handleInteraction = (interactionType: string) => {
    const finishTracking = trackTradingInteraction(flowType, interactionType);
    setTimeout(finishTracking, 16);
  };

  return (
    <div
      className={`trading-component ${className}`}
      data-trading-flow={flowType}
      onMouseEnter={() => handleInteraction('hover')}
      onFocus={() => handleInteraction('focus')}
      onClick={() => handleInteraction('click')}
    >
      {children}
    </div>
  );
}

/**
 * Performance-aware loading component
 */
export function PerformanceAwareLoader({
  isLoading,
  loadingText = 'Loading...',
  children,
  onLoadComplete,
}: {
  isLoading: boolean;
  loadingText?: string;
  children: React.ReactNode;
  onLoadComplete?: () => void;
}) {
  const loadStartTime = useRef<number | null>(null);

  useEffect(() => {
    if (isLoading && !loadStartTime.current) {
      loadStartTime.current = performance.now();
    } else if (!isLoading && loadStartTime.current) {
      const loadTime = performance.now() - loadStartTime.current;

      // Record loading performance
      import('@/utils/performance').then(({ performanceMonitor }) => {
        performanceMonitor.recordMetric({
          name: 'component_loading_time',
          value: loadTime,
          timestamp: Date.now(),
          tags: {
            component: 'PerformanceAwareLoader',
          },
        });
      });

      onLoadComplete?.();
      loadStartTime.current = null;
    }
  }, [isLoading, onLoadComplete]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-sm text-gray-600">{loadingText}</span>
      </div>
    );
  }

  return <>{children}</>;
}

/**
 * Performance Monitoring Hooks
 *
 * React hooks for tracking performance metrics in components
 * and trading-specific flows.
 */

import {
  performanceMonitor,
  recordApiCallTime,
  recordAuthenticationTime,
  recordChartRenderTime,
  recordSignalLoadTime,
  recordSubscriptionFlowTime,
} from '@/utils/performance';
import { useCallback, useEffect, useRef } from 'react';

/**
 * Hook to track component render performance
 */
export function useRenderPerformance(componentName: string) {
  const renderStartTime = useRef<number | undefined>(undefined);

  useEffect(() => {
    renderStartTime.current = performance.now();
  });

  useEffect(() => {
    if (renderStartTime.current) {
      const renderTime = performance.now() - renderStartTime.current;
      performanceMonitor.recordMetric({
        name: 'component_render_time',
        value: renderTime,
        timestamp: Date.now(),
        tags: {
          component: componentName,
        },
      });
    }
  });
}

/**
 * Hook to track signal loading performance
 */
export function useSignalLoadTracking() {
  const trackSignalLoad = useCallback((signalCount: number) => {
    const startTime = performance.now();

    return () => {
      recordSignalLoadTime(startTime, signalCount);
    };
  }, []);

  return trackSignalLoad;
}

/**
 * Hook to track authentication flow performance
 */
export function useAuthenticationTracking() {
  const trackAuthentication = useCallback(() => {
    const startTime = performance.now();

    return (success: boolean) => {
      recordAuthenticationTime(startTime, success);
    };
  }, []);

  return trackAuthentication;
}

/**
 * Hook to track subscription flow performance
 */
export function useSubscriptionTracking() {
  const trackSubscriptionStep = useCallback((step: string) => {
    const startTime = performance.now();

    return () => {
      recordSubscriptionFlowTime(startTime, step);
    };
  }, []);

  return trackSubscriptionStep;
}

/**
 * Hook to track API call performance
 */
export function useApiCallTracking() {
  const trackApiCall = useCallback((endpoint: string) => {
    const startTime = performance.now();

    return (success: boolean) => {
      recordApiCallTime(endpoint, startTime, success);
    };
  }, []);

  return trackApiCall;
}

/**
 * Hook to track chart rendering performance
 */
export function useChartRenderTracking() {
  const trackChartRender = useCallback((dataPoints: number) => {
    const startTime = performance.now();

    return () => {
      recordChartRenderTime(startTime, dataPoints);
    };
  }, []);

  return trackChartRender;
}

/**
 * Hook to track page navigation performance
 */
export function usePageNavigationTracking(pageName: string) {
  const navigationStartTime = useRef<number | undefined>(undefined);

  useEffect(() => {
    navigationStartTime.current = performance.now();

    return () => {
      if (navigationStartTime.current) {
        const navigationTime = performance.now() - navigationStartTime.current;
        performanceMonitor.recordMetric({
          name: 'page_navigation_time',
          value: navigationTime,
          timestamp: Date.now(),
          tags: {
            page: pageName,
          },
        });
      }
    };
  }, [pageName]);
}

/**
 * Hook to track user interaction performance
 */
export function useInteractionTracking() {
  const trackInteraction = useCallback((interactionType: string, elementId?: string) => {
    const startTime = performance.now();

    return () => {
      const interactionTime = performance.now() - startTime;
      performanceMonitor.recordMetric({
        name: 'user_interaction_time',
        value: interactionTime,
        timestamp: Date.now(),
        tags: {
          interaction_type: interactionType,
          element_id: elementId || 'unknown',
        },
      });
    };
  }, []);

  return trackInteraction;
}

/**
 * Hook to track data loading performance with error handling
 */
export function useDataLoadTracking() {
  const trackDataLoad = useCallback((dataType: string, itemCount?: number) => {
    const startTime = performance.now();

    return (success: boolean, error?: string) => {
      const loadTime = performance.now() - startTime;
      performanceMonitor.recordMetric({
        name: 'data_load_time',
        value: loadTime,
        timestamp: Date.now(),
        tags: {
          data_type: dataType,
          success: success.toString(),
          item_count: itemCount?.toString() || '0',
          error: error || 'none',
        },
      });
    };
  }, []);

  return trackDataLoad;
}

/**
 * Hook for performance budget monitoring with alerts
 */
export function usePerformanceBudgetMonitoring(thresholds?: Record<string, number>) {
  useEffect(() => {
    if (!thresholds) return;

    const checkBudgets = () => {
      const summary = performanceMonitor.getPerformanceSummary();

      Object.entries(thresholds).forEach(([metricName, threshold]) => {
        const budget = summary.budgets.find(b => b.name === metricName);
        if (budget && budget.current && budget.current > threshold) {
          console.warn(
            `Performance budget exceeded for ${metricName}: ${budget.current} > ${threshold}`
          );

          // Optional: Send alert to monitoring service
          if (process.env.NODE_ENV === 'production') {
            performanceMonitor.recordMetric({
              name: 'performance_budget_exceeded',
              value: budget.current,
              timestamp: Date.now(),
              tags: {
                metric_name: metricName,
                threshold: threshold.toString(),
                severity: budget.status,
              },
            });
          }
        }
      });
    };

    // Check budgets every 30 seconds
    const interval = setInterval(checkBudgets, 30000);

    return () => clearInterval(interval);
  }, [thresholds]);
}

/**
 * Hook to automatically track form submission performance
 */
export function useFormPerformanceTracking(formName: string) {
  const trackFormSubmission = useCallback(() => {
    const startTime = performance.now();

    return (success: boolean, validationErrors?: number) => {
      const submissionTime = performance.now() - startTime;
      performanceMonitor.recordMetric({
        name: 'form_submission_time',
        value: submissionTime,
        timestamp: Date.now(),
        tags: {
          form_name: formName,
          success: success.toString(),
          validation_errors: validationErrors?.toString() || '0',
        },
      });
    };
  }, [formName]);

  return trackFormSubmission;
}

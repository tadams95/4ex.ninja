/**
 * Animation Performance Monitoring Hook
 *
 * Tracks animation frame rate and performance for real-time optimization (1.10.6.3)
 */

import { recordAnimationPerformance } from '@/utils/performance';
import { useCallback, useEffect, useRef } from 'react';

interface AnimationFrameData {
  timestamp: number;
  frameTime: number;
}

/**
 * Hook to monitor animation performance and frame rate drops
 */
export function useAnimationPerformance(animationName: string, enabled: boolean = true) {
  const frameDataRef = useRef<AnimationFrameData[]>([]);
  const animationFrameIdRef = useRef<number | null>(null);
  const lastFrameTimeRef = useRef<number | null>(null);

  const startMonitoring = useCallback(() => {
    if (!enabled) return;

    const monitorFrame = (timestamp: number) => {
      if (lastFrameTimeRef.current !== null) {
        const frameTime = timestamp - lastFrameTimeRef.current;

        // Store frame data
        frameDataRef.current.push({ timestamp, frameTime });

        // Keep only last 60 frames (approximately 1 second at 60fps)
        if (frameDataRef.current.length > 60) {
          frameDataRef.current = frameDataRef.current.slice(-60);
        }

        // Record performance metrics
        recordAnimationPerformance(animationName, frameTime);
      }

      lastFrameTimeRef.current = timestamp;

      if (enabled) {
        animationFrameIdRef.current = requestAnimationFrame(monitorFrame);
      }
    };

    animationFrameIdRef.current = requestAnimationFrame(monitorFrame);
  }, [animationName, enabled]);

  const stopMonitoring = useCallback(() => {
    if (animationFrameIdRef.current) {
      cancelAnimationFrame(animationFrameIdRef.current);
      animationFrameIdRef.current = null;
    }
    lastFrameTimeRef.current = null;
  }, []);

  const getFrameStats = useCallback(() => {
    const frames = frameDataRef.current;
    if (frames.length === 0) return null;

    const frameTimes = frames.map(f => f.frameTime);
    const avgFrameTime = frameTimes.reduce((sum, time) => sum + time, 0) / frameTimes.length;
    const avgFps = 1000 / avgFrameTime;

    const droppedFrames = frameTimes.filter(time => time > 16.67).length; // 60fps = 16.67ms per frame
    const droppedFrameRate = (droppedFrames / frames.length) * 100;

    return {
      averageFrameTime: avgFrameTime,
      averageFps: avgFps,
      droppedFrames,
      droppedFrameRate,
      totalFrames: frames.length,
    };
  }, []);

  // Auto-start monitoring when enabled
  useEffect(() => {
    if (enabled) {
      startMonitoring();
    } else {
      stopMonitoring();
    }

    return stopMonitoring;
  }, [enabled, startMonitoring, stopMonitoring]);

  return {
    startMonitoring,
    stopMonitoring,
    getFrameStats,
  };
}

/**
 * Hook to monitor specific animation elements for performance
 */
export function useElementAnimationTracking(
  elementRef: React.RefObject<HTMLElement>,
  animationName: string
) {
  const observerRef = useRef<IntersectionObserver | null>(null);
  const { startMonitoring, stopMonitoring, getFrameStats } = useAnimationPerformance(
    animationName,
    false
  );

  useEffect(() => {
    if (!elementRef.current) return;

    observerRef.current = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            // Element is visible, start monitoring
            startMonitoring();
          } else {
            // Element is not visible, stop monitoring
            stopMonitoring();
          }
        });
      },
      { threshold: 0.1 }
    );

    observerRef.current.observe(elementRef.current);

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
      stopMonitoring();
    };
  }, [elementRef, startMonitoring, stopMonitoring]);

  return {
    getFrameStats,
  };
}

/**
 * Hook to track page transition animation performance
 */
export function usePageTransitionPerformance() {
  const transitionStartTime = useRef<number | null>(null);

  const startTransition = useCallback((transitionType: string) => {
    transitionStartTime.current = performance.now();
    // Start monitoring during transition
    return () => {
      if (transitionStartTime.current) {
        const duration = performance.now() - transitionStartTime.current;
        recordAnimationPerformance(`page_transition_${transitionType}`, duration);
        transitionStartTime.current = null;
      }
    };
  }, []);

  return {
    startTransition,
  };
}

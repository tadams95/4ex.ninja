/**
 * Performance Monitoring Utilities
 *
 * Comprehensive performance monitoring including Web Vitals,
 * custom metrics for trading flows, and performance budgets.
 */

import { onCLS, onFCP, onINP, onLCP, onTTFB, type Metric } from 'web-vitals';

// Performance thresholds (Google's Web Vitals recommendations)
export const PERFORMANCE_THRESHOLDS = {
  LCP: { good: 2500, needsImprovement: 4000 }, // Largest Contentful Paint
  INP: { good: 200, needsImprovement: 500 }, // Interaction to Next Paint
  CLS: { good: 0.1, needsImprovement: 0.25 }, // Cumulative Layout Shift
  FCP: { good: 1800, needsImprovement: 3000 }, // First Contentful Paint
  TTFB: { good: 800, needsImprovement: 1800 }, // Time to First Byte
} as const;

// Custom performance metrics for trading flows
export interface TradingPerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  tags?: Record<string, string>;
  userId?: string;
  sessionId?: string;
}

export interface PerformanceBudget {
  name: string;
  threshold: number;
  unit: 'ms' | 'kb' | 'score';
  current?: number;
  status: 'good' | 'needs-improvement' | 'poor';
}

class PerformanceMonitor {
  private metrics: TradingPerformanceMetric[] = [];
  private vitalsInitialized = false;
  private sessionId: string;

  constructor() {
    this.sessionId = this.generateSessionId();
    this.initializeWebVitals();
    this.initializeCustomMetrics();
  }

  private generateSessionId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private initializeWebVitals(): void {
    if (this.vitalsInitialized || typeof window === 'undefined') return;

    // Initialize Core Web Vitals monitoring
    onCLS(this.handleVital.bind(this));
    onINP(this.handleVital.bind(this));
    onFCP(this.handleVital.bind(this));
    onLCP(this.handleVital.bind(this));
    onTTFB(this.handleVital.bind(this));

    this.vitalsInitialized = true;
  }

  private handleVital(metric: Metric): void {
    const { name, value, rating } = metric;

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`Web Vital - ${name}:`, {
        value,
        rating,
        threshold: this.getThreshold(name),
      });
    }

    // Store metric
    this.recordMetric({
      name: `web_vital_${name.toLowerCase()}`,
      value,
      timestamp: Date.now(),
      tags: {
        rating,
        session_id: this.sessionId,
      },
    });

    // Send to analytics endpoint
    this.sendToAnalytics({
      type: 'web_vital',
      name,
      value,
      rating,
      sessionId: this.sessionId,
      url: window.location.pathname,
      userAgent: navigator.userAgent,
    });
  }

  private getThreshold(metricName: string): { good: number; needsImprovement: number } | null {
    const thresholds = PERFORMANCE_THRESHOLDS as any;
    return thresholds[metricName] || null;
  }

  private initializeCustomMetrics(): void {
    // Monitor page load performance
    if (typeof window !== 'undefined' && window.performance) {
      window.addEventListener('load', () => {
        setTimeout(() => {
          const navigation = performance.getEntriesByType(
            'navigation'
          )[0] as PerformanceNavigationTiming;

          if (navigation) {
            this.recordMetric({
              name: 'page_load_time',
              value: navigation.loadEventEnd - navigation.fetchStart,
              timestamp: Date.now(),
              tags: { url: window.location.pathname },
            });

            this.recordMetric({
              name: 'dom_content_loaded',
              value: navigation.domContentLoadedEventEnd - navigation.fetchStart,
              timestamp: Date.now(),
              tags: { url: window.location.pathname },
            });
          }
        }, 0);
      });
    }
  }

  // Trading-specific performance metrics
  public recordSignalLoadTime(startTime: number, signalCount: number): void {
    const duration = performance.now() - startTime;
    this.recordMetric({
      name: 'signal_load_time',
      value: duration,
      timestamp: Date.now(),
      tags: {
        signal_count: signalCount.toString(),
        session_id: this.sessionId,
      },
    });
  }

  public recordAuthenticationTime(startTime: number, success: boolean): void {
    const duration = performance.now() - startTime;
    this.recordMetric({
      name: 'authentication_time',
      value: duration,
      timestamp: Date.now(),
      tags: {
        success: success.toString(),
        session_id: this.sessionId,
      },
    });
  }

  public recordSubscriptionFlowTime(startTime: number, step: string): void {
    const duration = performance.now() - startTime;
    this.recordMetric({
      name: 'subscription_flow_time',
      value: duration,
      timestamp: Date.now(),
      tags: {
        step,
        session_id: this.sessionId,
      },
    });
  }

  public recordApiCallTime(endpoint: string, startTime: number, success: boolean): void {
    const duration = performance.now() - startTime;
    this.recordMetric({
      name: 'api_call_time',
      value: duration,
      timestamp: Date.now(),
      tags: {
        endpoint,
        success: success.toString(),
        session_id: this.sessionId,
      },
    });
  }

  public recordChartRenderTime(startTime: number, dataPoints: number): void {
    const duration = performance.now() - startTime;
    this.recordMetric({
      name: 'chart_render_time',
      value: duration,
      timestamp: Date.now(),
      tags: {
        data_points: dataPoints.toString(),
        session_id: this.sessionId,
      },
    });
  }

  // Record custom metric
  public recordMetric(metric: TradingPerformanceMetric): void {
    this.metrics.push(metric);

    // Keep only last 1000 metrics to prevent memory issues
    if (this.metrics.length > 1000) {
      this.metrics = this.metrics.slice(-1000);
    }

    // Log in development
    if (process.env.NODE_ENV === 'development') {
      console.log('Performance Metric:', metric);
    }
  }

  // Get current performance budget status
  public getPerformanceBudgets(): PerformanceBudget[] {
    const budgets: PerformanceBudget[] = [];

    // Check Web Vitals against thresholds
    const recentMetrics = this.getRecentMetrics(60000); // Last 60 seconds

    Object.entries(PERFORMANCE_THRESHOLDS).forEach(([vital, thresholds]) => {
      const metricName = `web_vital_${vital.toLowerCase()}`;
      const recentVital = recentMetrics.find(m => m.name === metricName);

      if (recentVital) {
        let status: 'good' | 'needs-improvement' | 'poor' = 'good';
        if (recentVital.value > thresholds.needsImprovement) {
          status = 'poor';
        } else if (recentVital.value > thresholds.good) {
          status = 'needs-improvement';
        }

        budgets.push({
          name: vital,
          threshold: thresholds.good,
          unit: vital === 'CLS' ? 'score' : 'ms',
          current: recentVital.value,
          status,
        });
      }
    });

    // Check custom performance budgets
    const avgSignalLoadTime = this.getAverageMetric('signal_load_time', 300000); // Last 5 minutes
    if (avgSignalLoadTime) {
      budgets.push({
        name: 'Signal Load Time',
        threshold: 2000, // 2 second budget
        unit: 'ms',
        current: avgSignalLoadTime,
        status:
          avgSignalLoadTime > 5000
            ? 'poor'
            : avgSignalLoadTime > 2000
            ? 'needs-improvement'
            : 'good',
      });
    }

    const avgApiCallTime = this.getAverageMetric('api_call_time', 300000);
    if (avgApiCallTime) {
      budgets.push({
        name: 'API Call Time',
        threshold: 1000, // 1 second budget
        unit: 'ms',
        current: avgApiCallTime,
        status:
          avgApiCallTime > 3000 ? 'poor' : avgApiCallTime > 1000 ? 'needs-improvement' : 'good',
      });
    }

    return budgets;
  }

  // Get metrics from the last N milliseconds
  public getRecentMetrics(timeWindow: number): TradingPerformanceMetric[] {
    const cutoff = Date.now() - timeWindow;
    return this.metrics.filter(metric => metric.timestamp > cutoff);
  }

  // Get average value for a metric type
  private getAverageMetric(metricName: string, timeWindow: number): number | null {
    const recentMetrics = this.getRecentMetrics(timeWindow).filter(
      metric => metric.name === metricName
    );

    if (recentMetrics.length === 0) return null;

    const sum = recentMetrics.reduce((acc, metric) => acc + metric.value, 0);
    return sum / recentMetrics.length;
  }

  // Send analytics data to backend
  private async sendToAnalytics(data: any): Promise<void> {
    try {
      // Only send in production or if explicitly enabled
      if (process.env.NODE_ENV !== 'production' && !process.env.NEXT_PUBLIC_ENABLE_ANALYTICS) {
        return;
      }

      await fetch('/api/analytics/performance', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
    } catch (error) {
      console.warn('Failed to send analytics data:', error);
    }
  }

  // Get performance summary
  public getPerformanceSummary(): {
    vitals: Record<string, number>;
    customMetrics: Record<string, number>;
    budgets: PerformanceBudget[];
    sessionId: string;
  } {
    const recentMetrics = this.getRecentMetrics(300000); // Last 5 minutes

    const vitals: Record<string, number> = {};
    const customMetrics: Record<string, number> = {};

    recentMetrics.forEach(metric => {
      if (metric.name.startsWith('web_vital_')) {
        const vitalName = metric.name.replace('web_vital_', '').toUpperCase();
        vitals[vitalName] = metric.value;
      } else {
        customMetrics[metric.name] = metric.value;
      }
    });

    return {
      vitals,
      customMetrics,
      budgets: this.getPerformanceBudgets(),
      sessionId: this.sessionId,
    };
  }
}

// Global performance monitor instance
export const performanceMonitor = new PerformanceMonitor();

// Export convenient functions
export const recordSignalLoadTime = (startTime: number, signalCount: number) =>
  performanceMonitor.recordSignalLoadTime(startTime, signalCount);

export const recordAuthenticationTime = (startTime: number, success: boolean) =>
  performanceMonitor.recordAuthenticationTime(startTime, success);

export const recordSubscriptionFlowTime = (startTime: number, step: string) =>
  performanceMonitor.recordSubscriptionFlowTime(startTime, step);

export const recordApiCallTime = (endpoint: string, startTime: number, success: boolean) =>
  performanceMonitor.recordApiCallTime(endpoint, startTime, success);

export const recordChartRenderTime = (startTime: number, dataPoints: number) =>
  performanceMonitor.recordChartRenderTime(startTime, dataPoints);

export const getPerformanceSummary = () => performanceMonitor.getPerformanceSummary();

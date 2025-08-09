/**
 * Performance Analytics API Endpoint
 *
 * Collects and stores performance metrics from the frontend
 * for analysis and monitoring.
 */

import { NextRequest, NextResponse } from 'next/server';

interface PerformanceMetric {
  type: 'web_vital' | 'custom_metric' | 'user_timing';
  name: string;
  value: number;
  rating?: string;
  sessionId: string;
  url: string;
  userAgent: string;
  timestamp?: number;
  tags?: Record<string, string>;
}

// In a real application, you'd store these in a database
const performanceMetrics: PerformanceMetric[] = [];

export async function POST(request: NextRequest) {
  try {
    const metric: PerformanceMetric = await request.json();

    // Validate required fields
    if (!metric.type || !metric.name || typeof metric.value !== 'number') {
      return NextResponse.json(
        { error: 'Missing required fields: type, name, value' },
        { status: 400 }
      );
    }

    // Add timestamp if not provided
    const enrichedMetric = {
      ...metric,
      timestamp: metric.timestamp || Date.now(),
    };

    // Store metric (in production, save to database)
    performanceMetrics.push(enrichedMetric);

    // Keep only last 10,000 metrics to prevent memory issues
    if (performanceMetrics.length > 10000) {
      performanceMetrics.splice(0, performanceMetrics.length - 10000);
    }

    // Log important metrics in development
    if (process.env.NODE_ENV === 'development') {
      console.log('Performance Metric Received:', {
        type: metric.type,
        name: metric.name,
        value: metric.value,
        rating: metric.rating,
        url: metric.url,
      });
    }

    // Check for performance issues and alert if needed
    await checkPerformanceThresholds(enrichedMetric);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error processing performance metric:', error);
    return NextResponse.json({ error: 'Failed to process metric' }, { status: 500 });
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const timeRange = searchParams.get('timeRange') || '1h';
    const metricType = searchParams.get('type');
    const sessionId = searchParams.get('sessionId');

    // Calculate time cutoff
    const cutoffTime = Date.now() - getTimeRangeMs(timeRange);

    // Filter metrics
    let filteredMetrics = performanceMetrics.filter(
      metric => metric.timestamp && metric.timestamp > cutoffTime
    );

    if (metricType) {
      filteredMetrics = filteredMetrics.filter(metric => metric.type === metricType);
    }

    if (sessionId) {
      filteredMetrics = filteredMetrics.filter(metric => metric.sessionId === sessionId);
    }

    // Generate summary statistics
    const summary = generateMetricsSummary(filteredMetrics);

    return NextResponse.json({
      metrics: filteredMetrics,
      summary,
      totalCount: filteredMetrics.length,
    });
  } catch (error) {
    console.error('Error retrieving performance metrics:', error);
    return NextResponse.json({ error: 'Failed to retrieve metrics' }, { status: 500 });
  }
}

function getTimeRangeMs(timeRange: string): number {
  switch (timeRange) {
    case '1m':
      return 60 * 1000;
    case '5m':
      return 5 * 60 * 1000;
    case '15m':
      return 15 * 60 * 1000;
    case '1h':
      return 60 * 60 * 1000;
    case '24h':
      return 24 * 60 * 60 * 1000;
    case '7d':
      return 7 * 24 * 60 * 60 * 1000;
    default:
      return 60 * 60 * 1000; // Default to 1 hour
  }
}

function generateMetricsSummary(metrics: PerformanceMetric[]) {
  const summary: Record<string, any> = {};

  // Group by metric name
  const groupedMetrics = metrics.reduce((acc, metric) => {
    if (!acc[metric.name]) {
      acc[metric.name] = [];
    }
    acc[metric.name].push(metric.value);
    return acc;
  }, {} as Record<string, number[]>);

  // Calculate statistics for each metric
  Object.entries(groupedMetrics).forEach(([name, values]) => {
    if (values.length === 0) return;

    const sorted = values.sort((a, b) => a - b);
    summary[name] = {
      count: values.length,
      min: Math.min(...values),
      max: Math.max(...values),
      avg: values.reduce((sum, val) => sum + val, 0) / values.length,
      median: sorted[Math.floor(sorted.length / 2)],
      p95: sorted[Math.floor(sorted.length * 0.95)],
      p99: sorted[Math.floor(sorted.length * 0.99)],
    };
  });

  return summary;
}

async function checkPerformanceThresholds(metric: PerformanceMetric) {
  // Define alerting thresholds
  const thresholds = {
    web_vital_lcp: 4000, // 4 seconds
    web_vital_cls: 0.25, // 0.25 score
    web_vital_inp: 500, // 500ms
    signal_load_time: 5000, // 5 seconds
    api_call_time: 3000, // 3 seconds
    chart_render_time: 2000, // 2 seconds
  };

  const threshold = thresholds[metric.name as keyof typeof thresholds];

  if (threshold && metric.value > threshold) {
    console.warn(`Performance threshold exceeded: ${metric.name} = ${metric.value} > ${threshold}`);

    // In production, you might want to send alerts to monitoring systems
    if (process.env.NODE_ENV === 'production') {
      // Example: Send to monitoring service
      // await sendAlert({
      //   type: 'performance_threshold_exceeded',
      //   metric: metric.name,
      //   value: metric.value,
      //   threshold,
      //   sessionId: metric.sessionId,
      //   url: metric.url,
      // });
    }
  }
}

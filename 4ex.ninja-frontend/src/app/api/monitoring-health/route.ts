/**
 * Health check endpoint for the monitoring proxy
 */

import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const monitoringApiBase = 'http://157.230.58.248:8081';
    const testEndpoint = `${monitoringApiBase}/regime/current`;

    console.log('[Monitoring Proxy Health] Testing connection to:', testEndpoint);

    const response = await fetch(testEndpoint, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(10000), // 10 second timeout
    });

    if (response.ok) {
      const data = await response.json();
      return NextResponse.json({
        status: 'healthy',
        proxyWorking: true,
        monitoringApiStatus: 'accessible',
        responseTime: response.headers.get('date'),
        sampleData: data,
        timestamp: new Date().toISOString(),
      });
    } else {
      return NextResponse.json(
        {
          status: 'degraded',
          proxyWorking: true,
          monitoringApiStatus: 'error',
          error: `HTTP ${response.status}: ${response.statusText}`,
          timestamp: new Date().toISOString(),
        },
        { status: response.status }
      );
    }
  } catch (error: any) {
    console.error('[Monitoring Proxy Health] Error:', error);

    return NextResponse.json(
      {
        status: 'unhealthy',
        proxyWorking: true,
        monitoringApiStatus: 'unreachable',
        error: error.message,
        errorType: error.name,
        timestamp: new Date().toISOString(),
      },
      { status: 503 }
    );
  }
}

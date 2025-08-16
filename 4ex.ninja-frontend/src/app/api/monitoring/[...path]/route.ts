/**
 * Next.js API Proxy for Monitoring Service
 * Solves CORS and mixed content issues by proxying requests server-side
 */

import { NextRequest, NextResponse } from 'next/server';

const MONITORING_API_BASE = 'http://157.230.58.248:8081';

export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  try {
    // Reconstruct the path from the dynamic route
    const path = params.path ? params.path.join('/') : '';
    const targetUrl = `${MONITORING_API_BASE}/${path}`;

    console.log(`[Monitoring Proxy] Proxying request to: ${targetUrl}`);

    // Forward the request to the monitoring API
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      // Add timeout to prevent hanging requests
      signal: AbortSignal.timeout(15000),
    });

    if (!response.ok) {
      console.error(`[Monitoring Proxy] API returned ${response.status}: ${response.statusText}`);
      return NextResponse.json(
        {
          error: 'Monitoring API unavailable',
          status: response.status,
          statusText: response.statusText,
          timestamp: new Date().toISOString(),
        },
        { status: response.status }
      );
    }

    // Get the response data
    const data = await response.json();

    // Return the data with proper CORS headers
    return NextResponse.json(data, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Accept',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
      },
    });
  } catch (error: any) {
    console.error('[Monitoring Proxy] Error:', error);

    // Handle different types of errors
    let errorMessage = 'Internal server error';
    let statusCode = 500;

    if (error.name === 'TimeoutError' || error.name === 'AbortError') {
      errorMessage = 'Request timeout - monitoring service may be slow or unavailable';
      statusCode = 504; // Gateway Timeout
    } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
      errorMessage = 'Cannot connect to monitoring service';
      statusCode = 503; // Service Unavailable
    }

    return NextResponse.json(
      {
        error: errorMessage,
        details: error.message,
        timestamp: new Date().toISOString(),
        isProxyError: true,
      },
      {
        status: statusCode,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Accept',
        },
      }
    );
  }
}

// Handle preflight OPTIONS requests
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Accept',
    },
  });
}

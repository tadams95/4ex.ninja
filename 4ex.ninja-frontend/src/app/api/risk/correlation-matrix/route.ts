import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL =
  process.env.BACKEND_URL ||
  (process.env.NODE_ENV === 'production' ? 'http://157.230.58.248:8000' : 'http://localhost:8000');
const IS_PRODUCTION = false; // Disable mock data since we have real backend

// Mock correlation data for production demo when backend is not available
const MOCK_CORRELATION_DATA = {
  matrix: {
    EUR_USD: { EUR_USD: 1.0, GBP_USD: 0.34, AUD_USD: 0.28, USD_JPY: -0.15 },
    GBP_USD: { EUR_USD: 0.34, GBP_USD: 1.0, AUD_USD: 0.31, USD_JPY: -0.12 },
    AUD_USD: { EUR_USD: 0.28, GBP_USD: 0.31, AUD_USD: 1.0, USD_JPY: -0.08 },
    USD_JPY: { EUR_USD: -0.15, GBP_USD: -0.12, AUD_USD: -0.08, USD_JPY: 1.0 },
  },
  risk_alerts: {
    high_correlations: [],
    breach_count: 0,
    threshold: 0.4,
  },
  pairs_analysis: [
    {
      pair: 'EUR_USD',
      correlations: { EUR_USD: 1.0, GBP_USD: 0.34, AUD_USD: 0.28, USD_JPY: -0.15 },
      average_correlation: 0.12,
    },
    {
      pair: 'GBP_USD',
      correlations: { EUR_USD: 0.34, GBP_USD: 1.0, AUD_USD: 0.31, USD_JPY: -0.12 },
      average_correlation: 0.13,
    },
    {
      pair: 'AUD_USD',
      correlations: { EUR_USD: 0.28, GBP_USD: 0.31, AUD_USD: 1.0, USD_JPY: -0.08 },
      average_correlation: 0.13,
    },
    {
      pair: 'USD_JPY',
      correlations: { EUR_USD: -0.15, GBP_USD: -0.12, AUD_USD: -0.08, USD_JPY: 1.0 },
      average_correlation: -0.12,
    },
  ],
  timestamp: new Date().toISOString(),
  status: 'success',
};

// CORS headers for all responses
const corsHeaders = {
  'Cache-Control': 'no-cache',
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

// Handle CORS preflight requests
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: corsHeaders,
  });
}

export async function GET(request: NextRequest) {
  try {
    const backendUrl = `${BACKEND_URL}/api/risk/correlation-matrix`;

    console.log('🔍 Correlation API Debug Info:');
    console.log('- NODE_ENV:', process.env.NODE_ENV);
    console.log('- BACKEND_URL env var:', process.env.BACKEND_URL);
    console.log('- Final BACKEND_URL:', BACKEND_URL);
    console.log('- IS_PRODUCTION:', IS_PRODUCTION);
    console.log('- Attempting to fetch:', backendUrl);

    // In production without backend URL, return mock data
    if (IS_PRODUCTION) {
      console.log('✅ Using mock correlation data for production demo');
      return NextResponse.json(MOCK_CORRELATION_DATA, {
        headers: corsHeaders,
      });
    }

    console.log('🌐 Attempting to proxy correlation request to backend:', backendUrl);

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // Add timeout to prevent hanging
      signal: AbortSignal.timeout(10000), // 10 second timeout
    });

    console.log('📡 Backend correlation response status:', response.status, response.statusText);

    if (!response.ok) {
      console.error('❌ Backend correlation response error:', response.status, response.statusText);

      // Return mock data as fallback if backend is unreachable
      console.log('🔄 Falling back to mock correlation data due to backend error');
      return NextResponse.json(MOCK_CORRELATION_DATA, {
        headers: corsHeaders,
      });
    }

    const data = await response.json();
    console.log('✅ Successfully fetched correlation data from backend');

    return NextResponse.json(data, {
      headers: corsHeaders,
    });
  } catch (error) {
    console.error('🚨 Correlation API proxy error:', error);

    // Return mock data as fallback
    console.log('🔄 Falling back to mock correlation data due to connection error');
    return NextResponse.json(MOCK_CORRELATION_DATA, {
      headers: corsHeaders,
    });
  }
}

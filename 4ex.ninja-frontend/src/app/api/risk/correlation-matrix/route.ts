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

export async function GET(request: NextRequest) {
  try {
    const backendUrl = `${BACKEND_URL}/api/risk/correlation-matrix`;

    console.log('🔍 Correlation API Debug Info:');
    console.log('- BACKEND_URL:', BACKEND_URL);
    console.log('- IS_PRODUCTION:', IS_PRODUCTION);
    console.log('- Attempting to fetch:', backendUrl);

    // In production without backend URL, return mock data
    if (IS_PRODUCTION) {
      console.log('✅ Using mock correlation data for production demo');
      return NextResponse.json(MOCK_CORRELATION_DATA, {
        headers: {
          'Cache-Control': 'no-cache',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        },
      });
    }

    console.log('🌐 Attempting to proxy correlation request to backend:', backendUrl);

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.error('Backend response error:', response.status, response.statusText);
      return NextResponse.json(
        { error: `Backend error: ${response.status} ${response.statusText}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, {
      headers: {
        'Cache-Control': 'no-cache',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });
  } catch (error) {
    console.error('Correlation API proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch correlation data from backend' },
      { status: 500 }
    );
  }
}

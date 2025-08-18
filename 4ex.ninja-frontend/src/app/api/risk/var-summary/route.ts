import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL =
  process.env.BACKEND_URL ||
  (process.env.NODE_ENV === 'production' ? 'http://157.230.58.248:8000' : 'http://localhost:8000');
const IS_PRODUCTION = false; // Disable mock data since we have real backend

// Mock data for production demo when backend is not available
const MOCK_VAR_DATA = {
  portfolio_var: {
    parametric: 38376.2,
    historical: 33670.64,
    monte_carlo: 38592.06,
    confidence_level: 0.95,
  },
  risk_metrics: {
    total_exposure: 50000.0,
    risk_utilization: 0.65,
    var_limit: 5000.0,
    breaches_today: 0,
  },
  position_breakdown: [
    { pair: 'EUR_USD', exposure: 10850.0, var_contribution: 0, pnl: 150.0 },
    { pair: 'GBP_USD', exposure: 10120.0, var_contribution: 0, pnl: -120.0 },
    { pair: 'AUD_USD', exposure: 8100.0, var_contribution: 0, pnl: 180.0 },
    { pair: 'USD_JPY', exposure: 2242500.0, var_contribution: 0, pnl: 300.0 },
  ],
  timestamp: new Date().toISOString(),
  status: 'success',
};

export async function GET(request: NextRequest) {
  try {
    // In production without backend URL, return mock data
    if (IS_PRODUCTION) {
      console.log('Using mock VaR data for production demo');
      return NextResponse.json(MOCK_VAR_DATA, {
        headers: {
          'Cache-Control': 'no-cache',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        },
      });
    }

    const url = new URL(request.url);
    const backendUrl = `${BACKEND_URL}/api/risk/var-summary`;

    console.log('Proxying request to:', backendUrl);

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
    console.error('API proxy error:', error);
    return NextResponse.json({ error: 'Failed to fetch data from backend' }, { status: 500 });
  }
}

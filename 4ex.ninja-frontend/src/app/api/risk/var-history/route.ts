// VaR Historical Data API Endpoint
// This endpoint provides historical VaR data for trend visualization
import { NextRequest, NextResponse } from 'next/server';

const PRODUCTION_BACKEND = 'http://157.230.58.248:8000';
const BACKEND_URL = PRODUCTION_BACKEND;

const corsHeaders = {
  'Cache-Control': 'no-cache',
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: corsHeaders,
  });
}

// Mock historical data for development/fallback
const generateMockHistoricalData = (period: string) => {
  const TARGET_VAR = 0.0031; // 0.31%
  const BASE_VAR = 0.0025;

  let dataPoints: Array<{
    timestamp: string;
    parametric: number;
    historical: number;
    monte_carlo: number;
    target: number;
  }> = [];

  const now = new Date();
  let intervals: number;
  let stepMinutes: number;

  switch (period) {
    case '1D':
      intervals = 24; // 24 hours
      stepMinutes = 60; // 1 hour intervals
      break;
    case '1W':
      intervals = 7; // 7 days
      stepMinutes = 1440; // 1 day intervals
      break;
    case '1M':
      intervals = 30; // 30 days
      stepMinutes = 1440; // 1 day intervals
      break;
    default:
      intervals = 24;
      stepMinutes = 60;
  }

  for (let i = intervals; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * stepMinutes * 60 * 1000);

    // Add some realistic variance (±20% around base VaR)
    const variance = (Math.random() - 0.5) * 0.4;
    const baseValue = BASE_VAR + BASE_VAR * variance;

    // Occasionally breach the target (10% chance)
    const shouldBreach = Math.random() < 0.1;
    const breachMultiplier = shouldBreach ? 1.2 + Math.random() * 0.3 : 1;

    dataPoints.push({
      timestamp: timestamp.toISOString(),
      parametric: baseValue * breachMultiplier * (1 + (Math.random() - 0.5) * 0.1),
      historical: baseValue * breachMultiplier * (1 + (Math.random() - 0.5) * 0.15),
      monte_carlo: baseValue * breachMultiplier * (1 + (Math.random() - 0.5) * 0.12),
      target: TARGET_VAR,
    });
  }

  return {
    period,
    data: dataPoints,
    summary: {
      total_points: dataPoints.length,
      breaches_count: dataPoints.filter(d => d.parametric > TARGET_VAR).length,
      avg_var: dataPoints.reduce((sum, d) => sum + d.parametric, 0) / dataPoints.length,
      max_var: Math.max(...dataPoints.map(d => d.parametric)),
      min_var: Math.min(...dataPoints.map(d => d.parametric)),
    },
    timestamp: new Date().toISOString(),
  };
};

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const period = searchParams.get('period') || '1D';

    // Try backend first
    try {
      const backendUrl = `${BACKEND_URL}/api/risk/var-history?period=${period}`;
      console.log(`[VarHistory] Attempting backend request: ${backendUrl}`);

      const response = await fetch(backendUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(5000),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('[VarHistory] ✅ Backend response successful');
        return NextResponse.json(data, { headers: corsHeaders });
      } else {
        console.log(`[VarHistory] ⚠️ Backend returned ${response.status}, using mock data`);
      }
    } catch (error) {
      console.log('[VarHistory] ⚠️ Backend error, using mock data:', error);
    }

    // Fallback to mock data
    const mockData = generateMockHistoricalData(period);
    console.log('[VarHistory] 📊 Returning mock historical data');

    return NextResponse.json(mockData, { headers: corsHeaders });
  } catch (error) {
    console.error('[VarHistory] ❌ API Error:', error);
    return NextResponse.json(
      {
        error: 'Failed to fetch VaR history',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500, headers: corsHeaders }
    );
  }
}

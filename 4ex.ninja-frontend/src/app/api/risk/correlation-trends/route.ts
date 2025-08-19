import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // Force production URL to match other working API routes
    const BACKEND_URL = 'http://157.230.58.248:8000';
    
    // Get query parameters
    const { searchParams } = new URL(request.url);
    const hoursBack = searchParams.get('hours_back') || '24';
    
    console.log('🔍 Correlation Trends API Debug Info:');
    console.log('- NODE_ENV:', process.env.NODE_ENV);
    console.log('- BACKEND_URL env var:', process.env.NEXT_PUBLIC_RISK_API_URL);
    console.log('- Final BACKEND_URL:', BACKEND_URL);
    console.log('- Hours back:', hoursBack);
    
    const backendUrl = `${BACKEND_URL}/api/risk/correlation-trends?hours_back=${hoursBack}`;
    console.log('- Attempting to fetch:', backendUrl);
    console.log('🌐 Attempting to proxy correlation trends request to backend:', backendUrl);

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      signal: AbortSignal.timeout(10000), // 10 second timeout
    });

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();
    console.log('📡 Backend correlation trends response status:', response.status, response.statusText);
    console.log('✅ Successfully fetched correlation trends data from backend');

    return NextResponse.json(data);
  } catch (error: any) {
    console.error('🚨 Correlation Trends API proxy error:', error);

    // Fallback to mock data when backend is unavailable
    console.log('🔄 Falling back to mock correlation trends data due to connection error');
    
    const hoursBack = parseInt(new URL(request.url).searchParams.get('hours_back') || '24');
    const mockTrendsData = {
      trends: [
        {
          timestamp: new Date().toISOString(),
          pair: "EUR_USD",
          correlation: 0.72,
          trend_direction: "increasing" as const,
          confidence: 0.85,
          predicted_correlation: 0.75,
          upper_bound: 0.82,
          lower_bound: 0.68,
          breach_probability: 0.15
        },
        {
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          pair: "GBP_USD",
          correlation: 0.68,
          trend_direction: "stable" as const,
          confidence: 0.78,
          predicted_correlation: 0.69,
          upper_bound: 0.75,
          lower_bound: 0.63,
          breach_probability: 0.22
        },
        {
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          pair: "USD_JPY",
          correlation: -0.45,
          trend_direction: "decreasing" as const,
          confidence: 0.82,
          predicted_correlation: -0.52,
          upper_bound: -0.38,
          lower_bound: -0.58,
          breach_probability: 0.18
        }
      ],
      total_points: 3,
      time_range: {
        start: new Date(Date.now() - hoursBack * 3600000).toISOString(),
        end: new Date().toISOString()
      },
      status: "mock_data"
    };

    return NextResponse.json(mockTrendsData);
  }
}

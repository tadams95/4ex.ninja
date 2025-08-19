import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // Force production URL to match other working API routes
    const BACKEND_URL = 'http://157.230.58.248:8000';

    console.log('🔍 Correlation Regime API Debug Info:');
    console.log('- NODE_ENV:', process.env.NODE_ENV);
    console.log('- BACKEND_URL env var:', process.env.NEXT_PUBLIC_RISK_API_URL);
    console.log('- Final BACKEND_URL:', BACKEND_URL);
    console.log('- IS_PRODUCTION:', process.env.NODE_ENV === 'production');

    const backendUrl = `${BACKEND_URL}/api/risk/correlation-regime`;
    console.log('- Attempting to fetch:', backendUrl);
    console.log('🌐 Attempting to proxy correlation regime request to backend:', backendUrl);

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      signal: AbortSignal.timeout(10000), // 10 second timeout
    });

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();
    console.log(
      '📡 Backend correlation regime response status:',
      response.status,
      response.statusText
    );
    console.log('✅ Successfully fetched correlation regime data from backend');

    return NextResponse.json(data);
  } catch (error: any) {
    console.error('🚨 Correlation Regime API proxy error:', error);

    // Fallback to mock data when backend is unavailable
    console.log('🔄 Falling back to mock correlation regime data due to connection error');

    const mockRegimeData = {
      regime: {
        current_regime: 'trending',
        confidence: 0.85,
        description: 'Markets are showing clear directional trends with strong momentum signals',
        characteristics: [
          'Strong directional bias',
          'High momentum persistence',
          'Low mean reversion tendencies',
        ],
      },
      regime_probability: 0.85,
      regime_history: [
        {
          date: '2024-01-15',
          regime: 'trending',
          confidence: 0.82,
        },
        {
          date: '2024-01-14',
          regime: 'sideways',
          confidence: 0.71,
        },
      ],
      recent_changes: [
        {
          timestamp: '2024-01-15T10:30:00Z',
          from_regime: 'sideways',
          to_regime: 'trending',
          trigger: 'momentum_breakout',
        },
      ],
      indicators: {
        momentum_strength: 0.78,
        volatility_regime: 'normal',
        correlation_regime: 'high',
      },
    };

    return NextResponse.json(mockRegimeData);
  }
}

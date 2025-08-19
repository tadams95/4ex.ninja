import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // Force production URL to match other working API routes
    const BACKEND_URL = 'http://157.230.58.248:8000';

    console.log('🔍 Correlation Forecast API Debug Info:');
    console.log('- NODE_ENV:', process.env.NODE_ENV);
    console.log('- BACKEND_URL env var:', process.env.NEXT_PUBLIC_RISK_API_URL);
    console.log('- Final BACKEND_URL:', BACKEND_URL);

    const backendUrl = `${BACKEND_URL}/api/risk/correlation-forecast`;
    console.log('- Attempting to fetch:', backendUrl);
    console.log('🌐 Attempting to proxy correlation forecast request to backend:', backendUrl);

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
      '📡 Backend correlation forecast response status:',
      response.status,
      response.statusText
    );
    console.log('✅ Successfully fetched correlation forecast data from backend');

    return NextResponse.json(data);
  } catch (error: any) {
    console.error('🚨 Correlation Forecast API proxy error:', error);

    // Fallback to mock data when backend is unavailable
    console.log('🔄 Falling back to mock correlation forecast data due to connection error');

    const mockForecastData = {
      forecasts: [
        {
          pair: 'EUR_USD',
          current_correlation: 0.72,
          predicted_values: [
            {
              timestamp: new Date(Date.now() + 3600000).toISOString(),
              value: 0.75,
              confidence_lower: 0.68,
              confidence_upper: 0.82,
            },
            {
              timestamp: new Date(Date.now() + 7200000).toISOString(),
              value: 0.78,
              confidence_lower: 0.7,
              confidence_upper: 0.86,
            },
            {
              timestamp: new Date(Date.now() + 10800000).toISOString(),
              value: 0.74,
              confidence_lower: 0.66,
              confidence_upper: 0.82,
            },
          ],
          breach_probability: 0.15,
          trend_strength: 0.82,
        },
        {
          pair: 'GBP_USD',
          current_correlation: 0.68,
          predicted_values: [
            {
              timestamp: new Date(Date.now() + 3600000).toISOString(),
              value: 0.69,
              confidence_lower: 0.62,
              confidence_upper: 0.76,
            },
            {
              timestamp: new Date(Date.now() + 7200000).toISOString(),
              value: 0.71,
              confidence_lower: 0.64,
              confidence_upper: 0.78,
            },
            {
              timestamp: new Date(Date.now() + 10800000).toISOString(),
              value: 0.67,
              confidence_lower: 0.6,
              confidence_upper: 0.74,
            },
          ],
          breach_probability: 0.22,
          trend_strength: 0.65,
        },
        {
          pair: 'USD_JPY',
          current_correlation: -0.45,
          predicted_values: [
            {
              timestamp: new Date(Date.now() + 3600000).toISOString(),
              value: -0.48,
              confidence_lower: -0.55,
              confidence_upper: -0.41,
            },
            {
              timestamp: new Date(Date.now() + 7200000).toISOString(),
              value: -0.52,
              confidence_lower: -0.59,
              confidence_upper: -0.45,
            },
            {
              timestamp: new Date(Date.now() + 10800000).toISOString(),
              value: -0.49,
              confidence_lower: -0.56,
              confidence_upper: -0.42,
            },
          ],
          breach_probability: 0.18,
          trend_strength: 0.73,
        },
      ],
      forecast_horizon_hours: 3,
      model_confidence: 0.78,
      last_updated: new Date().toISOString(),
      status: 'mock_data',
    };

    return NextResponse.json(mockForecastData);
  }
}

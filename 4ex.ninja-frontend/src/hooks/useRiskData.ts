/**
 * Custom hook for fetching and managing VaR risk data
 * Connects to the Phase 2 risk monitoring API
 */
import { useCallback, useEffect, useState } from 'react';

// VaR API configuration - following the regime monitoring pattern
const getApiBaseUrl = async () => {
  // Use environment variable if set
  if (process.env.NEXT_PUBLIC_RISK_API_URL) {
    console.log(`[RiskData] Using environment variable: ${process.env.NEXT_PUBLIC_RISK_API_URL}`);
    return process.env.NEXT_PUBLIC_RISK_API_URL;
  }

  // In development, try direct connection to droplet
  if (typeof window !== 'undefined' && window.location.protocol === 'http:') {
    console.log('[RiskData] Development mode - using direct droplet connection');
    return 'http://157.230.58.248:8000';
  }

  // In production (HTTPS), use Next.js API proxy to avoid CSP issues
  if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
    console.log('[RiskData] Production mode - using Next.js API proxy');
    return window.location.origin; // Use current domain with proxy routes
  }

  // Default fallback
  return window.location.origin;
};

// Initialize with default URL (will be updated after mount)
let API_BASE_URL = '';

export interface VaRData {
  portfolio_var: {
    parametric: number;
    historical: number;
    monte_carlo: number;
    confidence_level: number;
  };
  risk_metrics: {
    total_exposure: number;
    risk_utilization: number;
    var_limit: number;
    breaches_today: number;
  };
  position_breakdown: Array<{
    pair: string;
    exposure: number;
    var_contribution: number;
    pnl: number;
  }>;
  timestamp: string;
  status: string;
}

export interface CorrelationData {
  matrix: Record<string, Record<string, number | null>>;
  risk_alerts: {
    high_correlations: string[];
    breach_count: number;
    threshold: number;
  };
  pairs_analysis: Array<{
    pair: string;
    correlations: Record<string, number | null>;
    average_correlation: number | null;
  }>;
  timestamp: string;
  status: string;
}

export function useRiskData(refreshInterval: number = 30000) {
  const [varData, setVarData] = useState<VaRData | null>(null);
  const [correlationData, setCorrelationData] = useState<CorrelationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Initialize API URL async
  useEffect(() => {
    const initializeApi = async () => {
      API_BASE_URL = await getApiBaseUrl();
      console.log(`[RiskData] API Base URL set to: ${API_BASE_URL}`);
    };

    initializeApi();
  }, []);

  const fetchVaRData = useCallback(async () => {
    try {
      // Determine the correct endpoint based on environment
      const isProduction = window.location.protocol === 'https:';
      const endpoint = isProduction
        ? `${API_BASE_URL}/api/risk/var-summary` // Next.js proxy route
        : `${API_BASE_URL}/api/risk/var-summary`; // Direct to backend

      console.log(`[RiskData] Fetching VaR data from: ${endpoint}`);

      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        // Add timeout to prevent hanging
        signal: AbortSignal.timeout(10000),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log(`[RiskData] Successfully fetched VaR data:`, data);

      setVarData(data);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch VaR data';
      console.error('[RiskData] VaR fetch error:', errorMessage);
      setError(errorMessage);
    }
  }, []);

  const fetchCorrelationData = useCallback(async () => {
    try {
      // Determine the correct endpoint based on environment
      const isProduction = window.location.protocol === 'https:';
      const endpoint = isProduction
        ? `${API_BASE_URL}/api/risk/correlation-matrix` // Next.js proxy route
        : `${API_BASE_URL}/api/risk/correlation-matrix`; // Direct to backend

      console.log(`[RiskData] Fetching correlation data from: ${endpoint}`);

      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(10000),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log(`[RiskData] Successfully fetched correlation data:`, data);

      setCorrelationData(data);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch correlation data';
      console.error('[RiskData] Correlation fetch error:', errorMessage);
      setError(errorMessage);
    }
  }, []);

  const fetchAllData = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([fetchVaRData(), fetchCorrelationData()]);
      setLastUpdate(new Date());
    } finally {
      setLoading(false);
    }
  }, [fetchVaRData, fetchCorrelationData]);

  const refetch = useCallback(() => {
    fetchAllData();
  }, [fetchAllData]);

  // Initial fetch
  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // Set up auto-refresh interval
  useEffect(() => {
    if (refreshInterval > 0) {
      const interval = setInterval(fetchAllData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchAllData, refreshInterval]);

  return {
    varData,
    correlationData,
    loading,
    error,
    lastUpdate,
    refetch,
  };
}

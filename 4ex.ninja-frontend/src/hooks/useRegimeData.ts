/**
 * Custom hook for fetching and managing regime monitoring data
 * Connects to the Phase 2 monitoring API
 */
import { useCallback, useEffect, useState } from 'react';

// Dynamic API URL configuration for different environments
const getApiBaseUrl = () => {
  // Use environment variable if set
  if (process.env.NEXT_PUBLIC_MONITORING_API_URL) {
    return process.env.NEXT_PUBLIC_MONITORING_API_URL;
  }
  
  // For production deployments, try HTTPS first, fallback to HTTP
  if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
    return 'https://157.230.58.248:8081';
  }
  
  // Default to HTTP for development
  return 'http://157.230.58.248:8081';
};

const API_BASE_URL = getApiBaseUrl();

export interface RegimeStatus {
  current_regime: string;
  confidence: number;
  regime_strength: number;
  time_in_regime: number;
  last_change: string;
  volatility_level: string;
  trend_direction: string;
}

export interface Alert {
  id: string;
  alert_type: string;
  severity: 'info' | 'warning' | 'critical';
  title: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
  data?: any;
}

export interface StrategyHealth {
  health_score: number;
  status: string;
  warnings: string[];
  last_update: string;
  performance_metrics: {
    total_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    total_trades: number;
    current_positions: number;
  };
}

export interface PerformanceSummary {
  total_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  avg_trade_duration: number;
  total_trades: number;
  current_positions: number;
}

export const useRegimeData = () => {
  const [regimeStatus, setRegimeStatus] = useState<RegimeStatus | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [strategyHealth, setStrategyHealth] = useState<StrategyHealth | null>(null);
  const [performanceSummary, setPerformanceSummary] = useState<PerformanceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      console.log(`[RegimeData] Fetching data from: ${API_BASE_URL}`);

      // Helper function to safely parse JSON responses
      const safeJsonParse = async (response: Response, endpoint: string) => {
        try {
          const text = await response.text();
          console.log(`[RegimeData] Raw response from ${endpoint}:`, text.substring(0, 200));

          if (text.startsWith('<!DOCTYPE') || text.startsWith('<html')) {
            throw new Error(
              `${endpoint} returned HTML instead of JSON. API might be down or misconfigured.`
            );
          }

          return JSON.parse(text);
        } catch (parseError) {
          console.error(`[RegimeData] JSON parse error for ${endpoint}:`, parseError);
          throw parseError;
        }
      };

      // Enhanced request function with multiple fallback URLs and timeout
      const createRequest = async (endpoint: string) => {
        // Multiple URL options to try in order of preference
        const urlsToTry = [
          `${API_BASE_URL}${endpoint}`,
          `https://157.230.58.248:8081${endpoint}`,
          `http://157.230.58.248:8081${endpoint}`,
          // Add more fallback URLs if you have them
        ];

        const requestOptions: RequestInit = {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
          cache: 'no-cache',
          mode: 'cors',
          credentials: 'omit', // Don't send cookies to avoid CORS issues
        };

        // Try each URL with a timeout
        const tryUrl = async (url: string, timeout = 15000) => {
          console.log(`[RegimeData] Trying URL: ${url}`);
          
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), timeout);

          try {
            const response = await fetch(url, {
              ...requestOptions,
              signal: controller.signal,
            });
            clearTimeout(timeoutId);
            
            if (response.ok) {
              console.log(`[RegimeData] Success with URL: ${url}`);
              return response;
            }
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          } catch (error: any) {
            clearTimeout(timeoutId);
            
            // Handle different types of errors
            if (error.name === 'AbortError') {
              throw new Error(`Request timeout (${timeout}ms) for ${url}`);
            } else if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
              throw new Error(`Network error: Cannot connect to ${url} (CORS or server down)`);
            }
            throw error;
          }
        };

        let lastError: Error | null = null;
        
        // Try each URL in sequence
        for (const url of urlsToTry) {
          try {
            const response = await tryUrl(url);
            return response;
          } catch (error) {
            lastError = error instanceof Error ? error : new Error(String(error));
            console.warn(`[RegimeData] Failed URL ${url}:`, lastError.message);
          }
        }

        console.error(`[RegimeData] All URLs failed for ${endpoint}. Last error:`, lastError);

        // Return a mock response indicating the API is unavailable
        return new Response(
          JSON.stringify({
            error: `API unavailable: All URLs failed for ${endpoint}`,
            lastError: lastError?.message || 'Unknown error',
            timestamp: new Date().toISOString(),
            endpoint,
            availableEndpoints: [],
            isApiDown: true,
          }),
          {
            status: 503, // Service Unavailable
            headers: { 'Content-Type': 'application/json' },
          }
        );
      };

      // Fetch all data in parallel with individual error handling
      const [regimeRes, alertsRes, healthRes, performanceRes] = await Promise.all([
        createRequest('/regime/current'),
        createRequest('/alerts/recent'),
        createRequest('/strategy/health'),
        createRequest('/performance/summary'),
      ]);

      console.log(
        `[RegimeData] Response status: regime=${regimeRes.status}, alerts=${alertsRes.status}, health=${healthRes.status}, performance=${performanceRes.status}`
      );

      // Process regime data
      if (regimeRes.ok && regimeRes.status !== 503) {
        try {
          const regimeData = await safeJsonParse(regimeRes, '/regime/current');
          console.log('[RegimeData] Regime data:', regimeData);
          setRegimeStatus(regimeData);
        } catch (parseError) {
          console.error('[RegimeData] Failed to parse regime data:', parseError);
        }
      } else {
        console.error(
          '[RegimeData] Regime request failed:',
          regimeRes.status,
          regimeRes.statusText
        );
        // Check if it's an API unavailable response
        try {
          const errorData = await regimeRes.json();
          if (errorData.isApiDown) {
            setError(`Monitoring API is currently unavailable: ${errorData.lastError}`);
          }
        } catch (e) {
          // Ignore JSON parse errors for error responses
        }
      }

      // Process alerts data
      if (alertsRes.ok && alertsRes.status !== 503) {
        try {
          const alertsData = await safeJsonParse(alertsRes, '/alerts/recent');
          console.log('[RegimeData] Alerts data:', alertsData);
          setAlerts(alertsData.alerts || []);
        } catch (parseError) {
          console.error('[RegimeData] Failed to parse alerts data:', parseError);
        }
      } else {
        console.error(
          '[RegimeData] Alerts request failed:',
          alertsRes.status,
          alertsRes.statusText
        );
      }

      // Process health data
      if (healthRes.ok && healthRes.status !== 503) {
        try {
          const healthData = await safeJsonParse(healthRes, '/strategy/health');
          console.log('[RegimeData] Health data:', healthData);
          setStrategyHealth(healthData.health);
        } catch (parseError) {
          console.error('[RegimeData] Failed to parse health data:', parseError);
        }
      } else {
        console.error(
          '[RegimeData] Health request failed:',
          healthRes.status,
          healthRes.statusText
        );
      }

      // Process performance data
      if (performanceRes.ok && performanceRes.status !== 503) {
        try {
          const performanceData = await safeJsonParse(performanceRes, '/performance/summary');
          console.log('[RegimeData] Performance data:', performanceData);
          setPerformanceSummary(performanceData);
        } catch (parseError) {
          console.error('[RegimeData] Failed to parse performance data:', parseError);
        }
      } else {
        console.error(
          '[RegimeData] Performance request failed:',
          performanceRes.status,
          performanceRes.statusText
        );
      }

      setLastUpdate(new Date());
      console.log('[RegimeData] Data fetch completed successfully');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch data';
      console.error('[RegimeData] Fetch error:', err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const acknowledgeAlert = useCallback(async (alertId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/alerts/acknowledge/${alertId}`, {
        method: 'POST',
      });

      if (response.ok) {
        // Update local state
        setAlerts(prev =>
          prev.map(alert => (alert.id === alertId ? { ...alert, acknowledged: true } : alert))
        );
      }
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  }, []);

  // Auto-refresh data every 30 seconds
  useEffect(() => {
    const maxRetries = 3;

    // Initial fetch with improved retry logic
    const initialFetch = async () => {
      // Wait for page to fully load and any service workers to initialize
      await new Promise(resolve => setTimeout(resolve, 1000));

      const attemptFetch = async (attempt: number): Promise<void> => {
        try {
          console.log(`[RegimeData] Fetch attempt ${attempt + 1}/${maxRetries + 1}`);
          await fetchData();
          console.log('[RegimeData] Initial fetch successful');
        } catch (error) {
          console.error(`[RegimeData] Fetch attempt ${attempt + 1} failed:`, error);

          if (attempt < maxRetries) {
            const delay = Math.min(1000 * Math.pow(2, attempt), 5000); // Exponential backoff, max 5s
            console.log(`[RegimeData] Retrying in ${delay}ms...`);
            setTimeout(() => attemptFetch(attempt + 1), delay);
          } else {
            console.error('[RegimeData] All fetch attempts failed');
            setError('Failed to connect to monitoring API after multiple attempts. Please check if the monitoring service is running.');
            setLoading(false);
          }
        }
      };

      await attemptFetch(0);
    };

    initialFetch();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return {
    regimeStatus,
    alerts,
    strategyHealth,
    performanceSummary,
    loading,
    error,
    lastUpdate,
    refetch: fetchData,
    acknowledgeAlert,
  };
};

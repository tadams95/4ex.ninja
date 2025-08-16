/**
 * Custom hook for fetching and managing regime monitoring data
 * Connects to the Phase 2 monitoring API
 */

import { useCallback, useEffect, useState } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_MONITORING_API_URL || 'http://157.230.58.248:8081';

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

      // Create individual fetch requests with better error handling
      const createRequest = (endpoint: string) => {
        return fetch(`${API_BASE_URL}${endpoint}`, {
          method: 'GET',
          headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
          },
          cache: 'no-cache',
          mode: 'cors',
          credentials: 'omit', // Don't send cookies to avoid CORS issues
        }).catch(error => {
          console.error(`[RegimeData] Network error for ${endpoint}:`, error);
          // Return a mock response for failed requests to prevent Promise.all from failing
          return new Response(JSON.stringify({ error: `Network error: ${error.message}` }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' },
          });
        });
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
      if (regimeRes.ok && regimeRes.status !== 500) {
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
        // Log the response text for failed requests
        try {
          const errorText = await regimeRes.text();
          console.error('[RegimeData] Regime error response:', errorText.substring(0, 200));
        } catch (e) {
          console.error('[RegimeData] Could not read error response');
        }
      }

      // Process alerts data
      if (alertsRes.ok && alertsRes.status !== 500) {
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
      if (healthRes.ok && healthRes.status !== 500) {
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
      if (performanceRes.ok && performanceRes.status !== 500) {
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
    let retryCount = 0;
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
            setError('Failed to connect to monitoring API after multiple attempts');
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

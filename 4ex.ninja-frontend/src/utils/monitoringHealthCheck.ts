/**
 * Monitoring service health check utilities
 * Used to verify the monitoring API is accessible and properly configured
 */

export interface HealthCheckResult {
  isHealthy: boolean;
  status: 'healthy' | 'degraded' | 'unhealthy';
  endpoint: string;
  responseTime: number;
  error?: string;
  timestamp: string;
  details: {
    protocol: 'http' | 'https';
    statusCode?: number;
    hasData: boolean;
    corsEnabled: boolean;
  };
}

export interface ServiceEndpoint {
  name: string;
  url: string;
  protocol: 'http' | 'https';
  timeout: number;
}

class MonitoringHealthChecker {
  private baseUrls = [
    'https://157.230.58.248:8081',
    'http://157.230.58.248:8081',
  ];

  private endpoints = [
    '/regime/current',
    '/alerts/recent', 
    '/strategy/health',
    '/performance/summary',
  ];

  /**
   * Perform a quick health check on a single endpoint
   */
  async checkEndpoint(baseUrl: string, endpoint: string, timeout = 10000): Promise<HealthCheckResult> {
    const fullUrl = `${baseUrl}${endpoint}`;
    const startTime = Date.now();
    
    const result: HealthCheckResult = {
      isHealthy: false,
      status: 'unhealthy',
      endpoint: fullUrl,
      responseTime: 0,
      timestamp: new Date().toISOString(),
      details: {
        protocol: baseUrl.startsWith('https') ? 'https' : 'http',
        hasData: false,
        corsEnabled: false,
      },
    };

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(fullUrl, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        mode: 'cors',
        credentials: 'omit',
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      result.responseTime = Date.now() - startTime;
      result.details.statusCode = response.status;

      // Check CORS headers
      result.details.corsEnabled = response.headers.has('access-control-allow-origin');

      if (response.ok) {
        const data = await response.json();
        result.details.hasData = Object.keys(data).length > 0;
        result.isHealthy = true;
        result.status = 'healthy';
      } else {
        result.error = `HTTP ${response.status}: ${response.statusText}`;
        result.status = 'degraded';
      }

    } catch (error: any) {
      result.responseTime = Date.now() - startTime;
      
      if (error.name === 'AbortError') {
        result.error = `Timeout after ${timeout}ms`;
      } else if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
        result.error = `Network error: Cannot connect (CORS or server issue)`;
      } else {
        result.error = error.message || 'Unknown error';
      }
    }

    return result;
  }

  /**
   * Comprehensive health check of all endpoints and protocols
   */
  async performFullHealthCheck(): Promise<{
    overall: 'healthy' | 'degraded' | 'unhealthy';
    bestEndpoint?: string;
    results: HealthCheckResult[];
    recommendations: string[];
  }> {
    const results: HealthCheckResult[] = [];
    const recommendations: string[] = [];

    // Test all combinations of base URLs and endpoints
    for (const baseUrl of this.baseUrls) {
      for (const endpoint of this.endpoints) {
        const result = await this.checkEndpoint(baseUrl, endpoint);
        results.push(result);
      }
    }

    // Analyze results
    const healthyResults = results.filter(r => r.isHealthy);
    const httpResults = results.filter(r => r.details.protocol === 'http');
    const httpsResults = results.filter(r => r.details.protocol === 'https');

    let overall: 'healthy' | 'degraded' | 'unhealthy' = 'unhealthy';
    let bestEndpoint: string | undefined;

    if (healthyResults.length > 0) {
      // Find the best performing endpoint
      const bestResult = healthyResults.reduce((best, current) => 
        current.responseTime < best.responseTime ? current : best
      );
      bestEndpoint = bestResult.endpoint.replace(/\/[^\/]*$/, ''); // Remove endpoint path
      
      if (healthyResults.length === results.length) {
        overall = 'healthy';
      } else {
        overall = 'degraded';
      }
    }

    // Generate recommendations
    if (httpsResults.some(r => r.isHealthy) && httpResults.some(r => r.isHealthy)) {
      recommendations.push('Both HTTP and HTTPS are working - prefer HTTPS for production');
    } else if (httpResults.some(r => r.isHealthy)) {
      recommendations.push('Only HTTP is working - HTTPS has SSL/TLS configuration issues');
      recommendations.push('Consider fixing SSL certificate or use HTTP with proper security headers');
    } else if (httpsResults.some(r => r.isHealthy)) {
      recommendations.push('HTTPS is working correctly');
    } else {
      recommendations.push('No endpoints are accessible - check if monitoring service is running');
    }

    // CORS recommendations
    const corsIssues = results.filter(r => r.isHealthy && !r.details.corsEnabled);
    if (corsIssues.length > 0) {
      recommendations.push('CORS headers not detected - may cause issues in browser environments');
    }

    // Performance recommendations
    const slowResults = healthyResults.filter(r => r.responseTime > 5000);
    if (slowResults.length > 0) {
      recommendations.push(`Some endpoints are slow (>5s) - consider optimization`);
    }

    return {
      overall,
      bestEndpoint,
      results,
      recommendations,
    };
  }

  /**
   * Quick check to find the best available endpoint
   */
  async findBestEndpoint(): Promise<string | null> {
    for (const baseUrl of this.baseUrls) {
      try {
        const result = await this.checkEndpoint(baseUrl, '/regime/current', 5000);
        if (result.isHealthy) {
          return baseUrl;
        }
      } catch (error) {
        continue;
      }
    }
    return null;
  }

  /**
   * Continuous monitoring with callback
   */
  startContinuousMonitoring(
    callback: (result: HealthCheckResult) => void,
    intervalMs = 30000
  ): () => void {
    let isRunning = true;
    
    const monitor = async () => {
      if (!isRunning) return;
      
      const bestEndpoint = await this.findBestEndpoint();
      if (bestEndpoint) {
        const result = await this.checkEndpoint(bestEndpoint, '/regime/current');
        callback(result);
      } else {
        callback({
          isHealthy: false,
          status: 'unhealthy',
          endpoint: 'all endpoints',
          responseTime: 0,
          error: 'No endpoints available',
          timestamp: new Date().toISOString(),
          details: {
            protocol: 'http',
            hasData: false,
            corsEnabled: false,
          },
        });
      }
      
      if (isRunning) {
        setTimeout(monitor, intervalMs);
      }
    };

    monitor();

    return () => {
      isRunning = false;
    };
  }
}

// Export singleton instance
export const monitoringHealthChecker = new MonitoringHealthChecker();

// Utility function for quick health check in production
export async function quickHealthCheck(): Promise<boolean> {
  const result = await monitoringHealthChecker.findBestEndpoint();
  return result !== null;
}

// Utility function to get recommended API base URL
export async function getRecommendedApiBaseUrl(): Promise<string | null> {
  return await monitoringHealthChecker.findBestEndpoint();
}

/**
 * Monitoring Service Health Status Component
 * Displays real-time health status of the monitoring API
 */
import React, { useState, useEffect } from 'react';
import { monitoringHealthChecker, HealthCheckResult } from '../utils/monitoringHealthCheck';

interface HealthStatusProps {
  showDetails?: boolean;
  className?: string;
}

export const MonitoringHealthStatus: React.FC<HealthStatusProps> = ({
  showDetails = false,
  className = '',
}) => {
  const [healthResult, setHealthResult] = useState<HealthCheckResult | null>(null);
  const [isChecking, setIsChecking] = useState(true);
  const [showFullReport, setShowFullReport] = useState(false);

  useEffect(() => {
    let cleanup: (() => void) | null = null;

    // Start continuous monitoring
    cleanup = monitoringHealthChecker.startContinuousMonitoring((result) => {
      setHealthResult(result);
      setIsChecking(false);
    }, 30000); // Check every 30 seconds

    return () => {
      if (cleanup) cleanup();
    };
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'degraded':
        return 'text-yellow-600 bg-yellow-100';
      case 'unhealthy':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return '✅';
      case 'degraded':
        return '⚠️';
      case 'unhealthy':
        return '❌';
      default:
        return '⏳';
    }
  };

  const runFullHealthCheck = async () => {
    setIsChecking(true);
    const fullReport = await monitoringHealthChecker.performFullHealthCheck();
    console.log('Full Health Check Report:', fullReport);
    setShowFullReport(true);
    setIsChecking(false);
  };

  if (isChecking && !healthResult) {
    return (
      <div className={`p-4 border rounded-lg bg-gray-50 ${className}`}>
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900"></div>
          <span className="text-sm text-gray-600">Checking monitoring service...</span>
        </div>
      </div>
    );
  }

  if (!healthResult) {
    return null;
  }

  return (
    <div className={`p-4 border rounded-lg ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="text-lg">{getStatusIcon(healthResult.status)}</span>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-medium text-gray-900">Monitoring API</span>
              <span
                className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
                  healthResult.status
                )}`}
              >
                {healthResult.status.toUpperCase()}
              </span>
            </div>
            <div className="text-sm text-gray-500">
              Response time: {healthResult.responseTime}ms | {healthResult.details.protocol.toUpperCase()}
            </div>
          </div>
        </div>
        
        {showDetails && (
          <button
            onClick={runFullHealthCheck}
            disabled={isChecking}
            className="px-3 py-1 text-xs bg-blue-100 text-blue-600 rounded hover:bg-blue-200 disabled:opacity-50"
          >
            {isChecking ? 'Checking...' : 'Full Check'}
          </button>
        )}
      </div>

      {showDetails && healthResult.error && (
        <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          <strong>Error:</strong> {healthResult.error}
        </div>
      )}

      {showDetails && (
        <div className="mt-3 text-xs text-gray-500 space-y-1">
          <div>Endpoint: {healthResult.endpoint}</div>
          <div>Protocol: {healthResult.details.protocol}</div>
          <div>Has Data: {healthResult.details.hasData ? 'Yes' : 'No'}</div>
          <div>CORS Enabled: {healthResult.details.corsEnabled ? 'Yes' : 'No'}</div>
          <div>Last Check: {new Date(healthResult.timestamp).toLocaleTimeString()}</div>
        </div>
      )}
    </div>
  );
};

// Production deployment health check component
export const ProductionHealthCheck: React.FC = () => {
  const [fullReport, setFullReport] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const runProductionHealthCheck = async () => {
    setIsLoading(true);
    try {
      const report = await monitoringHealthChecker.performFullHealthCheck();
      setFullReport(report);
      
      // Log detailed report for debugging
      console.group('🏥 Production Health Check Report');
      console.log('Overall Status:', report.overall);
      console.log('Best Endpoint:', report.bestEndpoint);
      console.log('Recommendations:', report.recommendations);
      console.table(report.results.map(r => ({
        endpoint: r.endpoint,
        status: r.status,
        responseTime: `${r.responseTime}ms`,
        protocol: r.details.protocol,
        error: r.error || 'None',
      })));
      console.groupEnd();
      
    } catch (error) {
      console.error('Health check failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 border rounded-lg bg-white shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Production Health Check</h3>
        <button
          onClick={runProductionHealthCheck}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          {isLoading && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>}
          <span>{isLoading ? 'Checking...' : 'Run Health Check'}</span>
        </button>
      </div>

      {fullReport && (
        <div className="space-y-4">
          <div className={`p-3 rounded-lg ${
            fullReport.overall === 'healthy' ? 'bg-green-50 border border-green-200' :
            fullReport.overall === 'degraded' ? 'bg-yellow-50 border border-yellow-200' :
            'bg-red-50 border border-red-200'
          }`}>
            <div className="font-medium">
              Overall Status: <span className="uppercase">{fullReport.overall}</span>
            </div>
            {fullReport.bestEndpoint && (
              <div className="text-sm mt-1">
                Recommended Endpoint: <code className="bg-gray-100 px-2 py-1 rounded">{fullReport.bestEndpoint}</code>
              </div>
            )}
          </div>

          <div>
            <h4 className="font-medium mb-2">Recommendations:</h4>
            <ul className="space-y-1 text-sm">
              {fullReport.recommendations.map((rec: string, index: number) => (
                <li key={index} className="flex items-start space-x-2">
                  <span className="text-blue-500 mt-1">•</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="font-medium mb-2">Detailed Results:</h4>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Endpoint</th>
                    <th className="text-left p-2">Status</th>
                    <th className="text-left p-2">Response Time</th>
                    <th className="text-left p-2">Protocol</th>
                    <th className="text-left p-2">Error</th>
                  </tr>
                </thead>
                <tbody>
                  {fullReport.results.map((result: HealthCheckResult, index: number) => (
                    <tr key={index} className="border-b">
                      <td className="p-2 font-mono text-xs">{result.endpoint}</td>
                      <td className="p-2">
                        <span className={`px-2 py-1 rounded text-xs ${getStatusColor(result.status)}`}>
                          {result.status}
                        </span>
                      </td>
                      <td className="p-2">{result.responseTime}ms</td>
                      <td className="p-2 uppercase">{result.details.protocol}</td>
                      <td className="p-2 text-red-600 text-xs">{result.error || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  function getStatusColor(status: string) {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'degraded':
        return 'text-yellow-600 bg-yellow-100';
      case 'unhealthy':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  }
};

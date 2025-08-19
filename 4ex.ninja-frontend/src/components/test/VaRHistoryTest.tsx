// Quick test component to verify VaR History Hook
'use client';

import { useVaRHistory } from '../../hooks/useRiskData';

export default function VaRHistoryTest() {
  const { historyData, loading, error, lastUpdate, refetch } = useVaRHistory('1D', 0); // No auto-refresh for test

  console.log('[VaRHistoryTest] State:', {
    hasData: !!historyData,
    loading,
    error,
    lastUpdate: lastUpdate.toISOString(),
  });

  if (loading) {
    return (
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="text-lg font-semibold text-blue-800">Testing VaR History Hook</h3>
        <p className="text-blue-600">Loading historical VaR data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <h3 className="text-lg font-semibold text-red-800">❌ Hook Test Failed</h3>
        <p className="text-red-600">Error: {error}</p>
        <button
          onClick={refetch}
          className="mt-2 px-3 py-1 bg-red-100 text-red-800 rounded hover:bg-red-200"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!historyData) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <h3 className="text-lg font-semibold text-yellow-800">⚠️ No Data</h3>
        <p className="text-yellow-600">No historical data received</p>
      </div>
    );
  }

  return (
    <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
      <h3 className="text-lg font-semibold text-green-800">✅ VaR History Hook Test - SUCCESS</h3>
      <div className="mt-2 space-y-2 text-sm">
        <p>
          <strong>Period:</strong> {historyData.period}
        </p>
        <p>
          <strong>Data Points:</strong> {historyData.data.length}
        </p>
        <p>
          <strong>Breaches:</strong> {historyData.summary.breaches_count}
        </p>
        <p>
          <strong>Avg VaR:</strong> {(historyData.summary.avg_var * 100).toFixed(3)}%
        </p>
        <p>
          <strong>Max VaR:</strong> {(historyData.summary.max_var * 100).toFixed(3)}%
        </p>
        <p>
          <strong>Min VaR:</strong> {(historyData.summary.min_var * 100).toFixed(3)}%
        </p>
        <p>
          <strong>Last Update:</strong> {lastUpdate.toLocaleTimeString()}
        </p>
      </div>

      <div className="mt-3">
        <h4 className="font-medium text-green-700">Sample Data Points:</h4>
        <div className="grid grid-cols-2 gap-2 mt-1 text-xs">
          {historyData.data.slice(0, 4).map((point, index) => (
            <div key={index} className="bg-white p-2 rounded border">
              <p>
                <strong>Time:</strong> {new Date(point.timestamp).toLocaleTimeString()}
              </p>
              <p>
                <strong>Parametric:</strong> {(point.parametric * 100).toFixed(3)}%
              </p>
              <p>
                <strong>Historical:</strong> {(point.historical * 100).toFixed(3)}%
              </p>
              <p>
                <strong>Monte Carlo:</strong> {(point.monte_carlo * 100).toFixed(3)}%
              </p>
            </div>
          ))}
        </div>
      </div>

      <button
        onClick={refetch}
        className="mt-3 px-3 py-1 bg-green-100 text-green-800 rounded hover:bg-green-200"
      >
        Refresh Data
      </button>
    </div>
  );
}

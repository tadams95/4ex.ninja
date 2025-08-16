'use client';

import { useEffect, useState } from 'react';

const API_BASE_URL = 'http://157.230.58.248:8081';

export default function ApiTestPage() {
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const testApi = async () => {
      const endpoints = [
        '/regime/current',
        '/alerts/recent',
        '/strategy/health',
        '/performance/summary',
      ];

      const testResults = [];

      for (const endpoint of endpoints) {
        try {
          console.log(`Testing: ${API_BASE_URL}${endpoint}`);

          const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'GET',
            headers: {
              Accept: 'application/json',
              'Content-Type': 'application/json',
            },
            cache: 'no-cache',
            mode: 'cors',
            credentials: 'omit',
          });

          console.log(`Response status for ${endpoint}:`, response.status);

          const text = await response.text();
          console.log(`Raw response from ${endpoint}:`, text.substring(0, 200));

          let result;
          try {
            result = JSON.parse(text);
          } catch (e) {
            result = { error: 'JSON parse failed', text: text.substring(0, 100) };
          }

          testResults.push({
            endpoint,
            status: response.status,
            success: response.ok,
            data: result,
            headers: Object.fromEntries(response.headers.entries()),
          });
        } catch (error) {
          console.error(`Error testing ${endpoint}:`, error);
          testResults.push({
            endpoint,
            status: 'Network Error',
            success: false,
            error: error instanceof Error ? error.message : String(error),
            data: null,
          });
        }
      }

      setResults(testResults);
      setLoading(false);
    };

    testApi();
  }, []);

  if (loading) {
    return <div className="p-8">Testing API endpoints...</div>;
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">API Test Results</h1>

      {results.map((result, index) => (
        <div key={index} className="mb-6 p-4 border rounded-lg">
          <h2 className="text-lg font-semibold mb-2">
            {result.endpoint} - Status: {result.status}
          </h2>

          <div className="mb-2">
            <span
              className={`px-2 py-1 rounded text-sm ${
                result.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}
            >
              {result.success ? 'Success' : 'Failed'}
            </span>
          </div>

          {result.error && (
            <div className="mb-2">
              <strong>Error:</strong> {result.error}
            </div>
          )}

          {result.headers && (
            <details className="mb-2">
              <summary className="cursor-pointer font-medium">Response Headers</summary>
              <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-auto">
                {JSON.stringify(result.headers, null, 2)}
              </pre>
            </details>
          )}

          {result.data && (
            <details>
              <summary className="cursor-pointer font-medium">Response Data</summary>
              <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-auto">
                {JSON.stringify(result.data, null, 2)}
              </pre>
            </details>
          )}
        </div>
      ))}
    </div>
  );
}

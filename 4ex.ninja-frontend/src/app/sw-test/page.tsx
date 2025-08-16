'use client';

import { useEffect, useState } from 'react';

export default function ServiceWorkerTestPage() {
  const [swStatus, setSwStatus] = useState('');
  const [apiTest, setApiTest] = useState('');

  useEffect(() => {
    // Check service worker status
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.getRegistrations().then(registrations => {
        if (registrations.length === 0) {
          setSwStatus('✅ No service workers registered');
        } else {
          setSwStatus(
            `⚠️ ${registrations.length} service worker(s) found: ${registrations
              .map(r => r.scope)
              .join(', ')}`
          );
        }
      });
    } else {
      setSwStatus('❌ Service Worker not supported');
    }

    // Test API call
    const testApi = async () => {
      try {
        const response = await fetch('http://157.230.58.248:8081/health');
        const data = await response.json();
        setApiTest(`✅ API working: ${data.status}`);
      } catch (error) {
        setApiTest(`❌ API failed: ${error instanceof Error ? error.message : String(error)}`);
      }
    };

    testApi();
  }, []);

  const clearServiceWorkers = async () => {
    if ('serviceWorker' in navigator) {
      const registrations = await navigator.serviceWorker.getRegistrations();
      for (const registration of registrations) {
        await registration.unregister();
      }
      setSwStatus('✅ All service workers cleared');
      window.location.reload();
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Service Worker Debug</h1>

      <div className="space-y-4">
        <div className="p-4 border rounded">
          <h2 className="font-semibold mb-2">Service Worker Status</h2>
          <p>{swStatus}</p>
          <button
            onClick={clearServiceWorkers}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Clear All Service Workers
          </button>
        </div>

        <div className="p-4 border rounded">
          <h2 className="font-semibold mb-2">API Test</h2>
          <p>{apiTest}</p>
        </div>

        <div className="p-4 border rounded">
          <h2 className="font-semibold mb-2">Actions</h2>
          <div className="space-x-4">
            <a
              href="/regime-monitoring"
              className="inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Go to Monitoring Dashboard
            </a>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Reload Page
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

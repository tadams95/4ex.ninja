'use client';

import React, { useEffect, useState } from 'react';

interface OfflineErrorFallbackProps {
  onRetry?: () => void;
  showRetryButton?: boolean;
  children?: React.ReactNode;
}

export default function OfflineErrorFallback({
  onRetry,
  showRetryButton = true,
  children,
}: OfflineErrorFallbackProps) {
  const [isOnline, setIsOnline] = useState(true);
  const [hasTriedReconnect, setHasTriedReconnect] = useState(false);

  useEffect(() => {
    // Initial online status
    setIsOnline(navigator.onLine);

    // Listen for online/offline events
    const handleOnline = () => {
      setIsOnline(true);
      setHasTriedReconnect(false);
      // Auto-retry when coming back online
      if (onRetry && !hasTriedReconnect) {
        setTimeout(() => {
          onRetry();
          setHasTriedReconnect(true);
        }, 1000);
      }
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [onRetry, hasTriedReconnect]);

  const handleManualRetry = () => {
    setHasTriedReconnect(true);
    onRetry?.();
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col items-center text-center">
        {/* Offline Icon */}
        <div className={`rounded-full p-3 ${isOnline ? 'bg-green-100' : 'bg-red-100'}`}>
          {isOnline ? (
            <svg
              className="h-8 w-8 text-green-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0"
              />
            </svg>
          ) : (
            <svg
              className="h-8 w-8 text-red-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M18.364 5.636l-12.728 12.728m0-12.728l12.728 12.728"
              />
            </svg>
          )}
        </div>

        {/* Status Message */}
        <h3 className={`mt-4 text-lg font-medium ${isOnline ? 'text-green-900' : 'text-gray-900'}`}>
          {isOnline ? 'Connection Restored!' : "You're Offline"}
        </h3>

        <p className={`mt-2 text-sm ${isOnline ? 'text-green-700' : 'text-gray-600'}`}>
          {isOnline
            ? 'Your internet connection has been restored. You can now continue using the app.'
            : 'Please check your internet connection. Some features may not work properly while offline.'}
        </p>

        {/* Network Status Indicator */}
        <div className="mt-4 flex items-center space-x-2">
          <div className={`h-2 w-2 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-xs text-gray-500">{isOnline ? 'Online' : 'Offline'}</span>
        </div>

        {/* Action Buttons */}
        {showRetryButton && (
          <div className="mt-6 flex flex-col space-y-3 sm:flex-row sm:space-y-0 sm:space-x-3">
            <button
              type="button"
              onClick={handleManualRetry}
              disabled={!isOnline}
              className={`rounded-md px-4 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                isOnline
                  ? 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              {isOnline ? 'Try Again' : 'Waiting for Connection...'}
            </button>

            <button
              type="button"
              onClick={() => window.location.reload()}
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Reload Page
            </button>
          </div>
        )}

        {/* Additional Content */}
        {children && <div className="mt-6 w-full">{children}</div>}

        {/* Offline Tips */}
        {!isOnline && (
          <div className="mt-6 w-full rounded-md bg-gray-50 p-4">
            <h4 className="text-sm font-medium text-gray-900">While you're offline:</h4>
            <ul className="mt-2 text-sm text-gray-600">
              <li>• Some content may be cached and still available</li>
              <li>• New data won't load until connection is restored</li>
              <li>• Any changes you make may not be saved</li>
            </ul>
          </div>
        )}

        {/* Connection Troubleshooting */}
        {!isOnline && (
          <details className="mt-4 w-full">
            <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
              Connection troubleshooting
            </summary>
            <div className="mt-2 text-xs text-gray-500">
              <ul className="space-y-1">
                <li>• Check your WiFi or mobile data connection</li>
                <li>• Try refreshing the page</li>
                <li>• Check if other websites are working</li>
                <li>• Contact your internet service provider if the problem persists</li>
              </ul>
            </div>
          </details>
        )}
      </div>
    </div>
  );
}

/**
 * Hook to detect online/offline status
 */
export function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    setIsOnline(navigator.onLine);

    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}

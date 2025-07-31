'use client';

import React, { useState } from 'react';

interface ApiErrorFallbackProps {
  error?: Error | string;
  onRetry?: () => void;
  retryable?: boolean;
  title?: string;
  message?: string;
  className?: string;
}

/**
 * ApiErrorFallback - Component for handling API call failures
 * Provides retry mechanism and user-friendly error messages
 */
const ApiErrorFallback: React.FC<ApiErrorFallbackProps> = ({
  error,
  onRetry,
  retryable = true,
  title = 'Connection Error',
  message = 'Failed to load data. Please check your connection and try again.',
  className = '',
}) => {
  const [isRetrying, setIsRetrying] = useState(false);

  const handleRetry = async () => {
    if (!onRetry || isRetrying) return;

    setIsRetrying(true);
    try {
      await onRetry();
    } catch (err) {
      console.error('Retry failed:', err);
    } finally {
      setIsRetrying(false);
    }
  };

  const errorMessage = typeof error === 'string' ? error : error?.message || message;

  return (
    <div className={`bg-gray-900 border border-gray-700 rounded-lg p-6 text-center ${className}`}>
      {/* Warning Icon */}
      <div className="mb-4">
        <div className="mx-auto w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
          <svg
            className="w-6 h-6 text-yellow-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.982 16.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
        </div>
      </div>

      {/* Error Content */}
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
        <p className="text-gray-400 text-sm">{errorMessage}</p>
      </div>

      {/* Retry Button */}
      {retryable && onRetry && (
        <button
          onClick={handleRetry}
          disabled={isRetrying}
          className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded transition-colors"
        >
          {isRetrying ? (
            <span className="flex items-center justify-center">
              <svg
                className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Retrying...
            </span>
          ) : (
            'Try Again'
          )}
        </button>
      )}

      {/* Development Error Details */}
      {process.env.NODE_ENV === 'development' && error && typeof error !== 'string' && (
        <details className="mt-4 text-left">
          <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-400">
            Error Details (Dev)
          </summary>
          <pre className="mt-2 text-xs text-red-400 bg-gray-800 p-2 rounded overflow-auto max-h-24">
            {error.stack || error.toString()}
          </pre>
        </details>
      )}
    </div>
  );
};

export default ApiErrorFallback;

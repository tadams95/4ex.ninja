'use client';

import React, { memo, useCallback } from 'react';

interface PageErrorFallbackProps {
  error?: Error;
  resetError?: () => void;
  title?: string;
  message?: string;
}

/**
 * PageErrorFallback - Page-level error recovery component
 * Provides a user-friendly error display for page-level failures
 */
const PageErrorFallback: React.FC<PageErrorFallbackProps> = memo(
  ({
    error,
    resetError,
    title = 'Page Error',
    message = "This page encountered an error and couldn't load properly.",
  }) => {
    const handleRetry = useCallback(() => {
      if (resetError) {
        resetError();
      } else {
        // Fallback to page reload if no reset function provided
        window.location.reload();
      }
    }, [resetError]);

    const handleGoHome = () => {
      window.location.href = '/';
    };

    return (
      <div className="min-h-[60vh] flex items-center justify-center p-4">
        <div className="max-w-lg w-full text-center">
          {/* Error Icon */}
          <div className="mb-6">
            <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>

            <h1 className="text-2xl font-bold text-white mb-2">{title}</h1>
            <p className="text-gray-400">{message}</p>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <button
              onClick={handleRetry}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
            >
              Try Again
            </button>

            <button
              onClick={handleGoHome}
              className="w-full bg-gray-700 hover:bg-gray-600 text-white font-medium py-3 px-6 rounded-lg transition-colors"
            >
              Go to Home
            </button>
          </div>

          {/* Development Error Details */}
          {process.env.NODE_ENV === 'development' && error && (
            <details className="mt-6 text-left">
              <summary className="cursor-pointer text-sm text-gray-400 hover:text-gray-300 mb-2">
                Error Details (Development Only)
              </summary>
              <div className="text-xs text-red-400 bg-gray-900 p-3 rounded overflow-auto max-h-32">
                <div className="font-mono whitespace-pre-wrap">
                  {error.name}: {error.message}
                </div>
                {error.stack && <pre className="mt-2 text-red-300">{error.stack}</pre>}
              </div>
            </details>
          )}
        </div>
      </div>
    );
  }
);

export default PageErrorFallback;

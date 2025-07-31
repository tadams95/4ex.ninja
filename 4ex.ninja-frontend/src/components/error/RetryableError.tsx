'use client';

import { ApiError } from '@/utils/error-handler';
import React, { useState } from 'react';

interface RetryableErrorProps {
  error: ApiError;
  onRetry: () => void | Promise<void>;
  maxRetries?: number;
  children?: React.ReactNode;
}

export default function RetryableError({
  error,
  onRetry,
  maxRetries = 3,
  children,
}: RetryableErrorProps) {
  const [retryCount, setRetryCount] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);

  const handleRetry = async () => {
    if (retryCount >= maxRetries || isRetrying) return;

    setIsRetrying(true);
    setRetryCount(prev => prev + 1);

    try {
      await onRetry();
    } catch (retryError) {
      // Error will be handled by parent component
      console.warn('Retry failed:', retryError);
    } finally {
      setIsRetrying(false);
    }
  };

  const canRetry = retryCount < maxRetries && !isRetrying;
  const isNetworkError = !error.status || error.code === 'NETWORK_ERROR';
  const isServerError = error.status && error.status >= 500;
  const isRateLimited = error.status === 429;

  // Determine if this error type should show retry option
  const shouldShowRetry = isNetworkError || isServerError || isRateLimited;

  if (!shouldShowRetry) {
    return children ? (
      <>{children}</>
    ) : (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">{getErrorTitle(error)}</h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{getErrorMessage(error)}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-yellow-800">{getErrorTitle(error)}</h3>
          <div className="mt-2 text-sm text-yellow-700">
            <p>{getErrorMessage(error)}</p>
          </div>
          <div className="mt-4">
            <div className="flex space-x-3">
              <button
                type="button"
                onClick={handleRetry}
                disabled={!canRetry}
                className={`rounded-md px-3 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                  canRetry
                    ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200 focus:ring-yellow-500'
                    : 'bg-gray-100 text-gray-500 cursor-not-allowed'
                }`}
              >
                {isRetrying ? (
                  <span className="flex items-center">
                    <svg
                      className="animate-spin -ml-1 mr-2 h-4 w-4"
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
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Retrying...
                  </span>
                ) : (
                  `Try Again${retryCount > 0 ? ` (${maxRetries - retryCount} attempts left)` : ''}`
                )}
              </button>
              {children && <div className="text-sm text-yellow-700">{children}</div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function getErrorTitle(error: ApiError): string {
  if (!error.status || error.code === 'NETWORK_ERROR') {
    return 'Connection Problem';
  }

  if (error.status >= 500) {
    return 'Server Error';
  }

  if (error.status === 429) {
    return 'Rate Limit Exceeded';
  }

  return 'Request Failed';
}

function getErrorMessage(error: ApiError): string {
  if (!error.status || error.code === 'NETWORK_ERROR') {
    return 'Unable to connect to our servers. Please check your internet connection and try again.';
  }

  if (error.status >= 500) {
    return 'Our servers are experiencing issues. This is usually temporary.';
  }

  if (error.status === 429) {
    return "You're making requests too quickly. Please wait a moment before trying again.";
  }

  return error.message || 'An unexpected error occurred. Please try again.';
}

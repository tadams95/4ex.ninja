'use client';

import React, { Component, ReactNode } from 'react';

interface HydrationErrorBoundaryState {
  hasError: boolean;
  isHydrationError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

interface HydrationErrorBoundaryProps {
  children: ReactNode;
}

export default class HydrationErrorBoundary extends Component<
  HydrationErrorBoundaryProps,
  HydrationErrorBoundaryState
> {
  constructor(props: HydrationErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      isHydrationError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<HydrationErrorBoundaryState> {
    // Check if this is a hydration-related error
    const isHydrationError =
      error.message.includes('Hydration') ||
      error.message.includes('hydration') ||
      error.message.includes('server') ||
      error.message.includes('client') ||
      error.message.includes('Text content does not match') ||
      error.message.includes('Expected server HTML to contain');

    return {
      hasError: true,
      isHydrationError,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({
      errorInfo,
    });

    // Log hydration errors
    console.error('Hydration/SSR error:', error, errorInfo);

    // Special handling for hydration errors
    if (this.state.isHydrationError) {
      console.warn(
        'Hydration mismatch detected. This may cause layout shifts or functional issues.'
      );
    }

    // Log to error tracking service
    if (typeof window !== 'undefined') {
      try {
        const errorLog = {
          type: this.state.isHydrationError ? 'HYDRATION_ERROR' : 'SSR_ERROR',
          error: {
            name: error.name,
            message: error.message,
            stack: error.stack,
          },
          errorInfo,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
          url: window.location.href,
          isHydrationMismatch: this.state.isHydrationError,
        };

        // Store for debugging
        const existingErrors = JSON.parse(localStorage.getItem('hydrationErrors') || '[]');
        existingErrors.push(errorLog);
        if (existingErrors.length > 20) {
          existingErrors.shift(); // Keep only last 20 errors
        }
        localStorage.setItem('hydrationErrors', JSON.stringify(existingErrors));
      } catch {
        // Ignore localStorage errors
      }
    }
  }

  private handleRefresh = () => {
    window.location.reload();
  };

  private handleRetry = () => {
    this.setState({
      hasError: false,
      isHydrationError: false,
      error: null,
      errorInfo: null,
    });
  };

  private handleIgnore = () => {
    // For hydration errors, we can sometimes continue
    if (this.state.isHydrationError) {
      this.handleRetry();
    }
  };

  render() {
    if (this.state.hasError) {
      const { isHydrationError, error } = this.state;

      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-lg w-full bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <svg
                  className={`h-8 w-8 ${isHydrationError ? 'text-yellow-400' : 'text-red-400'}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  {isHydrationError ? (
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                    />
                  ) : (
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  )}
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-gray-900">
                  {isHydrationError ? 'Hydration Mismatch Detected' : 'Server Rendering Error'}
                </h3>
              </div>
            </div>

            <div className="mb-6">
              {isHydrationError ? (
                <div>
                  <p className="text-sm text-gray-600 mb-4">
                    The page content rendered on the server doesn't match what was expected on the
                    client. This can cause visual inconsistencies but usually doesn't prevent the
                    app from working.
                  </p>
                  <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3 mb-4">
                    <div className="flex">
                      <div className="flex-shrink-0">
                        <svg
                          className="h-4 w-4 text-yellow-400"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                        >
                          <path
                            fillRule="evenodd"
                            d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm text-yellow-700">
                          You can often continue using the app despite this warning.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-gray-600 mb-4">
                  There was an error during server-side rendering or client-side hydration. This
                  usually requires a page refresh to resolve.
                </p>
              )}

              <div className="bg-gray-50 rounded-md p-3 mb-4">
                <p className="text-xs text-gray-500 font-mono">
                  Error: {error?.message || 'Unknown rendering error'}
                </p>
              </div>
            </div>

            <div className="flex flex-col space-y-3 sm:flex-row sm:space-y-0 sm:space-x-3">
              {isHydrationError && (
                <button
                  onClick={this.handleIgnore}
                  className="flex-1 bg-yellow-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2"
                >
                  Continue Anyway
                </button>
              )}
              <button
                onClick={this.handleRetry}
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Try Again
              </button>
              <button
                onClick={this.handleRefresh}
                className="flex-1 bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
              >
                Refresh Page
              </button>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200">
              <details className="text-xs text-gray-500">
                <summary className="cursor-pointer hover:text-gray-700">Technical Details</summary>
                <div className="mt-2 space-y-2">
                  <div>
                    <strong>Error Type:</strong>{' '}
                    {isHydrationError ? 'Hydration Mismatch' : 'SSR Error'}
                  </div>
                  <div>
                    <strong>Error Name:</strong> {error?.name}
                  </div>
                  <div>
                    <strong>Component Stack:</strong>
                    <pre className="mt-1 whitespace-pre-wrap bg-gray-100 p-2 rounded text-xs">
                      {this.state.errorInfo?.componentStack}
                    </pre>
                  </div>
                </div>
              </details>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

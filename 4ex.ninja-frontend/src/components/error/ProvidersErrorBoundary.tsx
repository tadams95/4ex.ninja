'use client';

import React, { Component, ReactNode } from 'react';

interface ProvidersErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

interface ProvidersErrorBoundaryProps {
  children: ReactNode;
}

export default class ProvidersErrorBoundary extends Component<
  ProvidersErrorBoundaryProps,
  ProvidersErrorBoundaryState
> {
  constructor(props: ProvidersErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): ProvidersErrorBoundaryState {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // Log provider initialization errors
    console.error('Provider initialization error:', error, errorInfo);

    // TODO: Send to error tracking service
    if (typeof window !== 'undefined') {
      try {
        const errorLog = {
          type: 'PROVIDER_INITIALIZATION_ERROR',
          error: {
            name: error.name,
            message: error.message,
            stack: error.stack,
          },
          errorInfo,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
          url: window.location.href,
        };

        // Store for debugging
        const existingErrors = JSON.parse(localStorage.getItem('providerErrors') || '[]');
        existingErrors.push(errorLog);
        if (existingErrors.length > 10) {
          existingErrors.shift(); // Keep only last 10 errors
        }
        localStorage.setItem('providerErrors', JSON.stringify(existingErrors));
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
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <svg
                  className="h-8 w-8 text-red-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-gray-900">
                  Application Initialization Error
                </h3>
              </div>
            </div>

            <div className="mb-6">
              <p className="text-sm text-gray-600 mb-4">
                The application failed to initialize properly. This is usually a temporary issue
                with authentication or session management services.
              </p>

              <div className="bg-gray-50 rounded-md p-3 mb-4">
                <p className="text-xs text-gray-500 font-mono">
                  Error: {this.state.error?.message || 'Unknown initialization error'}
                </p>
              </div>
            </div>

            <div className="flex flex-col space-y-3 sm:flex-row sm:space-y-0 sm:space-x-3">
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
                    <strong>Error Name:</strong> {this.state.error?.name}
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

'use client';

import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  queryKey?: string;
}

/**
 * ReactQueryErrorBoundary - Wraps React Query components to handle query failures
 * Provides graceful fallbacks for subscription, crossover, and profile queries
 */
class ReactQueryErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      queryKey: error.message.includes('query') ? error.message : undefined,
    };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('ReactQueryErrorBoundary caught query error:', error, errorInfo);

    // Send to monitoring service
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'exception', {
        description: `React Query Error: ${error.message}`,
        fatal: false,
        query_key: this.state.queryKey || 'unknown',
      });
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, queryKey: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-[200px] flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200">
          <div className="text-center p-6 max-w-md">
            <div className="text-red-500 mb-4">
              <svg
                className="w-12 h-12 mx-auto"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Data Loading Error</h3>
            <p className="text-gray-600 mb-4 text-sm">
              We're having trouble loading your data. This might be due to a temporary network
              issue.
            </p>
            {this.state.queryKey && (
              <p className="text-xs text-gray-500 mb-4 font-mono">Query: {this.state.queryKey}</p>
            )}
            <div className="space-y-2">
              <button
                onClick={this.handleRetry}
                className="w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded text-sm font-medium transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.reload()}
                className="w-full bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm font-medium transition-colors"
              >
                Refresh Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ReactQueryErrorBoundary;

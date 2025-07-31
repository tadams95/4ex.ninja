'use client';

import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

/**
 * SubscribeButtonErrorBoundary - Wraps SubscribeButton to handle checkout flow errors
 * Provides graceful fallback when subscription/checkout fails
 */
class SubscribeButtonErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('SubscribeButtonErrorBoundary caught checkout flow error:', error, errorInfo);

    // Track checkout errors specifically
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
      // TODO: Send checkout error to monitoring service
      // trackError(error, { ...errorInfo, context: 'checkout_flow' });
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      // Compact error display for button component
      return (
        <div className="bg-red-900/30 border border-red-800 rounded-lg p-4 text-center">
          <div className="mb-2">
            <svg
              className="w-6 h-6 text-red-400 mx-auto mb-2"
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
            <p className="text-red-400 text-sm font-medium">Subscription Error</p>
            <p className="text-gray-400 text-xs mt-1">Unable to load subscription options</p>
          </div>

          <div className="space-y-2">
            <button
              onClick={this.handleRetry}
              className="w-full bg-green-600 hover:bg-green-700 text-white text-sm font-medium py-2 px-4 rounded transition-colors"
            >
              Try Again
            </button>

            <button
              onClick={() => (window.location.href = '/pricing')}
              className="w-full bg-gray-700 hover:bg-gray-600 text-white text-sm font-medium py-2 px-4 rounded transition-colors"
            >
              Go to Pricing
            </button>
          </div>

          {process.env.NODE_ENV === 'development' && this.state.error && (
            <details className="mt-3 text-left">
              <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-400">
                Error Details (Dev)
              </summary>
              <pre className="mt-1 text-xs text-red-400 bg-gray-800 p-2 rounded overflow-auto max-h-20">
                {this.state.error.toString()}
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default SubscribeButtonErrorBoundary;

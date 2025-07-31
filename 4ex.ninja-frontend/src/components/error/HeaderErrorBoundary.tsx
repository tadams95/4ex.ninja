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
 * HeaderErrorBoundary - Wraps Header to handle navigation and user status errors
 * Provides graceful fallback when header functionality fails
 */
class HeaderErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('HeaderErrorBoundary caught navigation/user status error:', error, errorInfo);

    // Track header errors specifically
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
      // TODO: Send header error to monitoring service
      // trackError(error, { ...errorInfo, context: 'navigation_header' });
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      // Simplified header fallback that maintains basic navigation
      return (
        <header className="bg-black border-b border-gray-800">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 items-center justify-between">
              {/* Logo/Brand */}
              <div className="flex items-center">
                <a href="/" className="text-green-400 text-xl font-bold">
                  4ex.ninja
                </a>
              </div>

              {/* Error indicator and basic navigation */}
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2 text-yellow-400">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.982 16.5c-.77.833.192 2.5 1.732 2.5z"
                    />
                  </svg>
                  <span className="text-sm">Navigation Error</span>
                </div>

                <button
                  onClick={this.handleRetry}
                  className="bg-green-600 hover:bg-green-700 text-white text-sm px-3 py-1 rounded transition-colors"
                >
                  Retry
                </button>

                {/* Basic navigation fallback */}
                <nav className="hidden md:flex space-x-4">
                  <a href="/" className="text-gray-300 hover:text-white text-sm">
                    Home
                  </a>
                  <a href="/feed" className="text-gray-300 hover:text-white text-sm">
                    Feed
                  </a>
                  <a href="/pricing" className="text-gray-300 hover:text-white text-sm">
                    Pricing
                  </a>
                  <a href="/login" className="text-gray-300 hover:text-white text-sm">
                    Login
                  </a>
                </nav>
              </div>
            </div>
          </div>

          {/* Development error details */}
          {process.env.NODE_ENV === 'development' && this.state.error && (
            <div className="bg-red-900/20 border-t border-red-800 px-4 py-2">
              <details>
                <summary className="cursor-pointer text-xs text-red-400 hover:text-red-300">
                  Header Error Details (Development Only)
                </summary>
                <pre className="mt-1 text-xs text-red-400 overflow-auto max-h-20">
                  {this.state.error.toString()}
                </pre>
              </details>
            </div>
          )}
        </header>
      );
    }

    return this.props.children;
  }
}

export default HeaderErrorBoundary;

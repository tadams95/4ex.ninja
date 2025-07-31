'use client';

import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasChunkError: boolean;
  retryCount: number;
}

/**
 * ChunkLoadErrorBoundary - Handles JavaScript chunk loading failures
 * Common in Next.js apps when deployments happen while users are browsing
 */
class ChunkLoadErrorBoundary extends Component<Props, State> {
  private maxRetries = 3;

  constructor(props: Props) {
    super(props);
    this.state = {
      hasChunkError: false,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> | null {
    // Check if it's a chunk loading error
    if (
      error.name === 'ChunkLoadError' ||
      error.message.includes('ChunkLoadError') ||
      error.message.includes('Loading chunk') ||
      error.message.includes('Loading CSS chunk')
    ) {
      return { hasChunkError: true };
    }

    // Not a chunk error, let it bubble up to other error boundaries
    return null;
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Only handle chunk load errors
    if (
      error.name === 'ChunkLoadError' ||
      error.message.includes('ChunkLoadError') ||
      error.message.includes('Loading chunk') ||
      error.message.includes('Loading CSS chunk')
    ) {
      console.warn('ChunkLoadErrorBoundary caught a chunk loading error:', error);

      // Auto-reload after a short delay if under retry limit
      if (this.state.retryCount < this.maxRetries) {
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      }
    } else {
      // Re-throw non-chunk errors
      throw error;
    }
  }

  handleManualReload = () => {
    window.location.reload();
  };

  handleRetry = () => {
    this.setState(prevState => ({
      hasChunkError: false,
      retryCount: prevState.retryCount + 1,
    }));
  };

  render() {
    if (this.state.hasChunkError) {
      return (
        <div className="min-h-screen bg-black text-white flex items-center justify-center p-4">
          <div className="max-w-md w-full text-center">
            <div className="mb-6">
              {/* Update Icon */}
              <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <svg
                  className="w-8 h-8 text-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
              </div>

              <h1 className="text-2xl font-bold text-green-400 mb-2">Update Available</h1>
              <p className="text-gray-400 mb-4">
                A new version of the application is available. Please refresh your browser to get
                the latest updates.
              </p>

              {this.state.retryCount >= this.maxRetries && (
                <p className="text-yellow-400 text-sm mb-4">
                  Multiple refresh attempts detected. You may need to clear your browser cache.
                </p>
              )}
            </div>

            <div className="space-y-3">
              <button
                onClick={this.handleManualReload}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
              >
                Refresh Now
              </button>

              {this.state.retryCount < this.maxRetries && (
                <button
                  onClick={this.handleRetry}
                  className="w-full bg-gray-700 hover:bg-gray-600 text-white font-medium py-3 px-6 rounded-lg transition-colors"
                >
                  Try Again Without Refresh
                </button>
              )}
            </div>

            {this.state.retryCount >= this.maxRetries && (
              <div className="mt-6 p-4 bg-gray-900 rounded-lg text-left">
                <h3 className="text-sm font-medium text-yellow-400 mb-2">Troubleshooting:</h3>
                <ul className="text-xs text-gray-400 space-y-1">
                  <li>• Clear your browser cache and cookies</li>
                  <li>• Try opening the site in an incognito/private window</li>
                  <li>• Check your internet connection</li>
                  <li>• Contact support if the problem persists</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ChunkLoadErrorBoundary;

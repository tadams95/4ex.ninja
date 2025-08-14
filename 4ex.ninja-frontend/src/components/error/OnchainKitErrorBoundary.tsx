'use client';

import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class OnchainKitErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log the error for debugging
    console.error('OnchainKit Error:', error, errorInfo);

    // Filter out known OnchainKit analytics errors
    if (
      error.message?.includes('Failed to fetch') &&
      errorInfo.componentStack?.includes('handleSendAnalytics')
    ) {
      // Silently handle analytics errors
      return;
    }

    // Handle CSP-related errors
    if (
      error.message?.includes('Content Security Policy') ||
      error.message?.includes('CSP') ||
      error.message?.includes('Refused to connect')
    ) {
      console.warn('CSP-related error detected, attempting graceful fallback');
      return;
    }
  }

  render() {
    if (this.state.hasError) {
      // Check if it's an analytics-related error
      if (this.state.error?.message?.includes('Failed to fetch')) {
        // For analytics errors, just render children without the error
        return this.props.children;
      }

      // Check if it's a CSP-related error
      if (
        this.state.error?.message?.includes('Content Security Policy') ||
        this.state.error?.message?.includes('CSP') ||
        this.state.error?.message?.includes('Refused to connect')
      ) {
        // For CSP errors, log and continue rendering
        console.warn('CSP error handled gracefully:', this.state.error?.message);
        return this.props.children;
      }

      // For other errors, show fallback UI
      return (
        this.props.fallback || (
          <div className="p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-800">Something went wrong with the wallet connection.</p>
            <button
              onClick={() => this.setState({ hasError: false })}
              className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Try again
            </button>
          </div>
        )
      );
    }

    return this.props.children;
  }
}

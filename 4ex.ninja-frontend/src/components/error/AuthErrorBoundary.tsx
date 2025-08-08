'use client';

import { Component, ErrorInfo, ReactNode } from 'react';
import PageErrorFallback from './PageErrorFallback';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

/**
 * AuthErrorBoundary - Wraps authentication pages to handle auth failures
 * Provides specific fallback UI for authentication-related errors
 */
class AuthErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('AuthErrorBoundary caught authentication error:', error, errorInfo);

    // Track authentication errors specifically
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
      // TODO: Send auth error to monitoring service
      // trackError(error, { ...errorInfo, context: 'authentication' });
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      return (
        <PageErrorFallback
          error={this.state.error}
          resetError={this.handleReset}
          title="Authentication Error"
          message="There was a problem with the authentication system. Please try again or contact support if the issue persists."
        />
      );
    }

    return this.props.children;
  }
}

export default AuthErrorBoundary;

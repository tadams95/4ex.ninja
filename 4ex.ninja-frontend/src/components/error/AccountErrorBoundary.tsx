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
 * AccountErrorBoundary - Wraps Account page to handle subscription management errors
 * Provides specific fallback UI for account/subscription-related errors
 */
class AccountErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('AccountErrorBoundary caught subscription management error:', error, errorInfo);

    // Track subscription management errors specifically
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
      // TODO: Send subscription error to monitoring service
      // trackError(error, { ...errorInfo, context: 'subscription_management' });
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
          title="Account Management Error"
          message="Unable to load your account information. This could be due to a connection issue with our subscription service."
        />
      );
    }

    return this.props.children;
  }
}

export default AccountErrorBoundary;

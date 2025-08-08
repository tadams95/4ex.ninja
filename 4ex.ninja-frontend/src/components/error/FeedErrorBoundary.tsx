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
 * FeedErrorBoundary - Wraps Feed page to handle signal loading failures
 * Provides specific fallback UI for signal-related errors
 */
class FeedErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('FeedErrorBoundary caught signal loading error:', error, errorInfo);

    // Track signal loading errors specifically
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
      // TODO: Send signal loading error to monitoring service
      // trackError(error, { ...errorInfo, context: 'signal_loading' });
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
          title="Signal Loading Error"
          message="Unable to load trading signals. This could be due to a network issue or temporary service interruption."
        />
      );
    }

    return this.props.children;
  }
}

export default FeedErrorBoundary;

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
 * PricingErrorBoundary - Wraps Pricing page to handle Stripe integration failures
 * Provides specific fallback UI for payment/checkout-related errors
 */
class PricingErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('PricingErrorBoundary caught Stripe integration error:', error, errorInfo);

    // Track Stripe/payment errors specifically
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
      // TODO: Send payment error to monitoring service
      // trackError(error, { ...errorInfo, context: 'stripe_integration' });
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
          title="Payment System Error"
          message="There was an issue connecting to our payment system. Please try again in a few moments or contact support."
        />
      );
    }

    return this.props.children;
  }
}

export default PricingErrorBoundary;

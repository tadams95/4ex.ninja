'use client';

import { ProtectedRouteErrorBoundary } from '@/components/error';
import { useAuth } from '@/hooks/api';
import { BaseComponentProps } from '@/types';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

interface ProtectedRouteProps extends BaseComponentProps {
  requireSubscription?: boolean;
}

interface SubscriptionResponse {
  isSubscribed: boolean;
}

function ProtectedRouteComponent({ requireSubscription = true, children }: ProtectedRouteProps) {
  const router = useRouter();
  const { isAuthenticated, loading } = useAuth();
  const [verified, setVerified] = useState<boolean>(false);
  const [subscriptionStatus, setSubscriptionStatus] = useState<boolean | null>(null);
  const [isCheckingAPI, setIsCheckingAPI] = useState<boolean>(false);

  // Get subscription status directly from MongoDB API for reliable data
  useEffect(() => {
    if (isAuthenticated && requireSubscription && subscriptionStatus === null && !isCheckingAPI) {
      setIsCheckingAPI(true);

      fetch('/api/subscription-status')
        .then(res => res.json())
        .then((data: SubscriptionResponse) => {
          setSubscriptionStatus(data.isSubscribed);
        })
        .catch(err => {
          console.error('Error checking subscription status:', err);
          setSubscriptionStatus(false); // Assume not subscribed on error
        })
        .finally(() => {
          setIsCheckingAPI(false);
        });
    }
  }, [isAuthenticated, requireSubscription, subscriptionStatus, isCheckingAPI]);

  // Make access decisions based on auth and subscription status
  useEffect(() => {
    // Wait until auth status is determined
    if (loading) return;

    // Handle unauthenticated users
    if (!isAuthenticated) {
      router.push(`/login?callbackUrl=${encodeURIComponent(window.location.href)}`);
      return;
    }

    // Now we know user is authenticated

    // For routes that don't require subscription
    if (!requireSubscription) {
      setVerified(true);
      return;
    }

    // For routes that require subscription, wait for API check to complete
    if (subscriptionStatus !== null) {
      if (subscriptionStatus) {
        setVerified(true);
      } else {
        // User not subscribed, redirect to pricing
        router.push('/pricing');
      }
    }
    // Otherwise wait for API check to complete
  }, [loading, isAuthenticated, requireSubscription, router, subscriptionStatus]);

  // Show loading state during auth or subscription check
  if (loading || !verified || (requireSubscription && subscriptionStatus === null)) {
    return (
      <div className="flex justify-center items-center h-screen bg-black">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-green-500"></div>
      </div>
    );
  }

  // We've verified all requirements, render the protected content
  return children;
}

export default function ProtectedRoute(props: ProtectedRouteProps) {
  return (
    <ProtectedRouteErrorBoundary>
      <ProtectedRouteComponent {...props} />
    </ProtectedRouteErrorBoundary>
  );
}

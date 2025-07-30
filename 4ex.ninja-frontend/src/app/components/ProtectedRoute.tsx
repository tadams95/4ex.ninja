'use client';

import { BaseComponentProps, User } from '@/types';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

interface ProtectedRouteProps extends BaseComponentProps {
  requireSubscription?: boolean;
}

interface SubscriptionResponse {
  isSubscribed: boolean;
}

export default function ProtectedRoute({
  requireSubscription = true,
  children,
}: ProtectedRouteProps) {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [verified, setVerified] = useState<boolean>(false);
  const [subscriptionStatus, setSubscriptionStatus] = useState<boolean | null>(null);
  const [isCheckingAPI, setIsCheckingAPI] = useState<boolean>(false);

  // Get subscription status directly from API for reliable data
  useEffect(() => {
    if (
      status === 'authenticated' &&
      requireSubscription &&
      subscriptionStatus === null &&
      !isCheckingAPI
    ) {
      setIsCheckingAPI(true);

      fetch('/api/subscription-status')
        .then(res => res.json())
        .then((data: SubscriptionResponse) => {
          // console.log("Subscription API response:", data);
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
  }, [status, requireSubscription, subscriptionStatus, isCheckingAPI]);

  // Make access decisions based on auth and subscription status
  useEffect(() => {
    // Wait until auth status is determined
    if (status === 'loading') return;

    // Handle unauthenticated users
    if (status === 'unauthenticated') {
      router.push(`/login?callbackUrl=${encodeURIComponent(window.location.href)}`);
      return;
    }

    // Now we know user is authenticated

    // For routes that don't require subscription
    if (!requireSubscription) {
      setVerified(true);
      return;
    }

    // For routes that require subscription

    // First check session data
    const sessionSubscribed = (session?.user as User)?.isSubscribed === true;

    // Then check API data (more reliable)
    const apiSubscribed = subscriptionStatus === true;

    // If either source confirms subscription, allow access
    if (sessionSubscribed || apiSubscribed) {
      // console.log("User is subscribed, allowing access", {
      //   sessionSubscribed,
      //   apiSubscribed
      // });
      setVerified(true);
    }
    // Only redirect if we've completed API check and user is not subscribed
    else if (subscriptionStatus !== null) {
      // console.log("User not subscribed, redirecting to /pricing");
      router.push('/pricing');
    }
    // Otherwise wait for API check to complete
  }, [session, status, requireSubscription, router, subscriptionStatus]);

  // Show loading state during auth or subscription check
  if (status === 'loading' || !verified || (requireSubscription && subscriptionStatus === null)) {
    return (
      <div className="flex justify-center items-center h-screen bg-black">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-green-500"></div>
      </div>
    );
  }

  // We've verified all requirements, render the protected content
  return children;
}

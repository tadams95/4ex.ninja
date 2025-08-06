'use client';

import { SubscribeButtonErrorBoundary } from '@/components/error';
import { useAuth } from '@/hooks/api';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

function SubscribeButtonComponent() {
  const [loading, setLoading] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [checkingStatus, setCheckingStatus] = useState(true);
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();

  useEffect(() => {
    // Only check subscription status if user is logged in
    if (isAuthenticated) {
      checkSubscriptionStatus();
    } else if (!authLoading) {
      setCheckingStatus(false);
    }
  }, [isAuthenticated, authLoading]);

  const checkSubscriptionStatus = async () => {
    try {
      const response = await fetch('/api/subscription-status');
      if (response.ok) {
        const data = await response.json();
        setIsSubscribed(data.isSubscribed);
      } else {
        console.error('Failed to fetch subscription status');
      }
    } catch (error) {
      console.error('Error checking subscription:', error);
    } finally {
      setCheckingStatus(false);
    }
  };

  const handleButtonClick = () => {
    setLoading(true);

    if (!isAuthenticated) {
      // Not logged in - go to login
      router.push('/login');
    } else if (isSubscribed) {
      // Subscribed - go to feed
      router.push('/feed');
    } else {
      // Logged in but not subscribed - go to register/subscribe
      router.push('/register');
    }
  };

  // Decide button text based on auth and subscription status
  const getButtonText = () => {
    if (loading) return 'Loading...';
    if (authLoading || checkingStatus) return 'Loading...';
    if (!isAuthenticated) return 'Sign In';
    if (isSubscribed) return 'Go to Feed';
    return 'Start 1-Month Free Trial';
  };

  return (
    <button
      onClick={handleButtonClick}
      disabled={loading || authLoading || checkingStatus}
      className="bg-green-700 hover:bg-green-900 text-white font-bold py-2 px-4 rounded"
    >
      {getButtonText()}
    </button>
  );
}

export default function SubscribeButton() {
  return (
    <SubscribeButtonErrorBoundary>
      <SubscribeButtonComponent />
    </SubscribeButtonErrorBoundary>
  );
}

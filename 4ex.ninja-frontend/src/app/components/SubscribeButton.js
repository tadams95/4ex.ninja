"use client";

import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";

export default function SubscribeButton() {
  const [loading, setLoading] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [checkingStatus, setCheckingStatus] = useState(true);
  const router = useRouter();
  const { data: session, status } = useSession();

  useEffect(() => {
    // Only check subscription status if user is logged in
    if (status === 'authenticated' && session?.user?.id) {
      checkSubscriptionStatus();
    } else if (status !== 'loading') {
      setCheckingStatus(false);
    }
  }, [session, status]);

  const checkSubscriptionStatus = async () => {
    try {
      const response = await fetch('/api/subscription-status');
      if (response.ok) {
        const data = await response.json();
        setIsSubscribed(data.isSubscribed);
        console.log('Subscription status:', data);
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
    
    if (!session) {
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
    if (loading) return "Loading...";
    if (status === 'loading' || checkingStatus) return "Loading...";
    if (!session) return "Sign In";
    if (isSubscribed) return "Go to Feed";
    return "Start 1-Month Free Trial";
  };

  return (
    <button
      onClick={handleButtonClick}
      disabled={loading || status === 'loading' || checkingStatus}
      className="bg-green-700 hover:bg-green-900 text-white font-bold py-2 px-4 rounded"
    >
      {getButtonText()}
    </button>
  );
}

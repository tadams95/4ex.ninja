"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function ProtectedRoute({
  requireSubscription = false,
  children,
}) {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [subscriptionLoading, setSubscriptionLoading] = useState(true);
  const router = useRouter();
  
  // Fetch subscription status directly from MongoDB
  useEffect(() => {
    const fetchSubscriptionStatus = async () => {
      if (isAuthenticated) {
        setSubscriptionLoading(true);
        try {
          const response = await fetch("/api/subscription-status");
          
          if (!response.ok) {
            throw new Error("Failed to fetch subscription status");
          }
          
          const data = await response.json();
          setIsSubscribed(data.isSubscribed);
        } catch (error) {
          console.error("Error fetching subscription status:", error);
          // In case of error, we assume not subscribed for security
          setIsSubscribed(false);
        } finally {
          setSubscriptionLoading(false);
        }
      }
    };
    
    if (isAuthenticated && requireSubscription) {
      fetchSubscriptionStatus();
    } else if (isAuthenticated && !requireSubscription) {
      // If subscription not required, skip loading
      setSubscriptionLoading(false);
    }
  }, [isAuthenticated, requireSubscription]);

  // Handle routing based on auth and subscription status
  useEffect(() => {
    const handleRouting = async () => {
      if (!authLoading) {
        if (!isAuthenticated) {
          router.push(
            "/login?callbackUrl=" + encodeURIComponent(window.location.href)
          );
        } else if (requireSubscription && !subscriptionLoading && !isSubscribed) {
          router.push("/pricing");
        }
      }
    };
    
    handleRouting();
  }, [isAuthenticated, isSubscribed, authLoading, subscriptionLoading, requireSubscription, router]);

  // Show loading state while checking auth or subscription
  if (authLoading || (requireSubscription && subscriptionLoading)) {
    return (
      <div className="flex justify-center items-center h-screen bg-black">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-green-500"></div>
      </div>
    );
  }

  // Only render children when authentication requirements are met
  if (
    (isAuthenticated && !requireSubscription) ||
    (isAuthenticated && requireSubscription && isSubscribed)
  ) {
    return children;
  }

  return null;
}

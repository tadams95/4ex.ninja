"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { useSession } from "next-auth/react";

export default function ProtectedRoute({
  requireSubscription = true,
  children,
}) {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const { data: session } = useSession();
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [subscriptionLoading, setSubscriptionLoading] = useState(true);
  const router = useRouter();
  
  // Log session info for debugging
  useEffect(() => {
    if (session) {
      console.log("Session in ProtectedRoute:", {
        email: session.user.email,
        isSubscribed: session.user.isSubscribed
      });
    }
  }, [session]);
  
  // First check if subscription status is in the session
  useEffect(() => {
    if (session?.user?.isSubscribed !== undefined) {
      setIsSubscribed(!!session.user.isSubscribed);
      setSubscriptionLoading(false);
      console.log("Using subscription status from session:", !!session.user.isSubscribed);
    }
  }, [session]);
  
  // Fetch subscription status from MongoDB as a backup
  useEffect(() => {
    const fetchSubscriptionStatus = async () => {
      // Skip if we already have the info from session
      if (!subscriptionLoading || session?.user?.isSubscribed !== undefined) {
        return;
      }
      
      if (isAuthenticated) {
        try {
          const response = await fetch("/api/subscription-status");
          
          if (!response.ok) {
            throw new Error("Failed to fetch subscription status");
          }
          
          const data = await response.json();
          console.log("Subscription API response:", data);
          
          setIsSubscribed(!!data.isSubscribed);
        } catch (error) {
          console.error("Error fetching subscription status:", error);
          setIsSubscribed(false);
        } finally {
          setSubscriptionLoading(false);
        }
      }
    };
    
    if (isAuthenticated && requireSubscription && subscriptionLoading) {
      fetchSubscriptionStatus();
    } else if (isAuthenticated && !requireSubscription) {
      setSubscriptionLoading(false);
    }
  }, [isAuthenticated, requireSubscription, subscriptionLoading, session]);

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

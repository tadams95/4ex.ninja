"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";

export default function ProtectedRoute({ requireSubscription = true, children }) {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [verified, setVerified] = useState(false);
  const [subscriptionData, setSubscriptionData] = useState(null);

  useEffect(() => {
    // Always fetch subscription status directly from API
    // This bypasses any session state issues
    if (status === "authenticated" && requireSubscription) {
      fetch("/api/subscription-status")
        .then(res => res.json())
        .then(data => {
          console.log("Direct subscription status check:", data);
          setSubscriptionData(data);
        })
        .catch(err => {
          console.error("Error checking status:", err);
          // Assume not subscribed on error
          setSubscriptionData({ isSubscribed: false });
        });
    }
  }, [status, requireSubscription]);

  useEffect(() => {
    // Wait until session loads
    if (status === "loading") return;

    if (status === "unauthenticated") {
      router.push(`/login?callbackUrl=${encodeURIComponent(window.location.href)}`);
      return;
    }

    // For subscription-protected routes, use the API data directly
    if (requireSubscription) {
      // First try the session
      const sessionSubscribed = session?.user?.isSubscribed;
      console.log("Session subscription status:", sessionSubscribed);
      
      // Then try direct API data
      const apiSubscribed = subscriptionData?.isSubscribed;
      console.log("API subscription status:", apiSubscribed);
      
      // Use either source of truth
      if (sessionSubscribed === true || apiSubscribed === true) {
        console.log("User is subscribed from either source, allowing access");
        setVerified(true);
      } else if (subscriptionData !== null) {
        // Only redirect if we've actually checked the API
        console.log("User not subscribed, redirecting to /pricing");
        router.push("/pricing");
      }
    } else {
      // Non-subscription routes just need authentication
      setVerified(true);
    }
  }, [session, status, requireSubscription, router, subscriptionData]);

  if (status === "loading" || (requireSubscription && subscriptionData === null) || !verified) {
    return (
      <div className="flex justify-center items-center h-screen bg-black">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-green-500"></div>
      </div>
    );
  }

  return children;
}

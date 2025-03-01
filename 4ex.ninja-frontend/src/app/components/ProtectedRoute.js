"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";

export default function ProtectedRoute({
  requireSubscription = true,
  children,
}) {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [verified, setVerified] = useState(false);
  
  useEffect(() => {
    // Debug the session info
    if (session) {
      console.log("Protected Route - Session:", {
        authenticated: status === "authenticated",
        email: session.user.email,
        isSubscribed: session.user.isSubscribed
      });
    }
    
    // Handle authentication check
    if (status === "unauthenticated") {
      router.push(`/login?callbackUrl=${encodeURIComponent(window.location.href)}`);
      return;
    }
    
    // Handle subscription check
    if (status === "authenticated") {
      if (requireSubscription && session.user.isSubscribed !== true) {
        console.log("User not subscribed, redirecting to pricing", {
          isSubscribed: session.user.isSubscribed
        });
        router.push("/pricing");
        return;
      }
      
      // User is authenticated and has required subscription
      setVerified(true);
    }
  }, [session, status, requireSubscription, router]);

  // Show loading state
  if (status === "loading" || !verified) {
    return (
      <div className="flex justify-center items-center h-screen bg-black">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-green-500"></div>
      </div>
    );
  }

  // Safe to render protected content
  return children;
}

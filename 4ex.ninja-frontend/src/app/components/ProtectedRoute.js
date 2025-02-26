"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function ProtectedRoute({
  requireSubscription = false,
  children,
}) {
  const { isAuthenticated, isSubscribed, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading) {
      if (!isAuthenticated) {
        router.push(
          "/login?callbackUrl=" + encodeURIComponent(window.location.href)
        );
      } else if (requireSubscription && !isSubscribed) {
        router.push("/pricing");
      }
    }
  }, [isAuthenticated, isSubscribed, loading, requireSubscription, router]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
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

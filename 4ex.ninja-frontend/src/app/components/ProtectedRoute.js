"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";

export default function ProtectedRoute({ requireSubscription = true, children }) {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [verified, setVerified] = useState(false);

  // Add debugging
  useEffect(() => {
    if (session) {
      console.log("ProtectedRoute session:", {
        email: session.user.email,
        requiresSubscription: requireSubscription,
        isSubscribed: session.user.isSubscribed,
      });
    }
  }, [session, requireSubscription]);

  useEffect(() => {
    if (status === "loading") return;

    if (status === "unauthenticated") {
      router.push(`/login?callbackUrl=${encodeURIComponent(window.location.href)}`);
      return;
    }

    // TEMPORARY FIX: Allow all authenticated users through
    // Remove this when subscription checking is fixed
    if (status === "authenticated") {
      console.log("Allowing authenticated user access (temporary fix)");
      setVerified(true);
      return;
    }

    /*
    // This is the proper implementation to use once subscription checking is fixed
    if (requireSubscription) {
      if (session?.user?.isSubscribed) {
        setVerified(true);
      } else {
        router.push("/pricing");
      }
    } else {
      setVerified(true);
    }
    */
  }, [session, status, requireSubscription, router]);

  if (status === "loading" || !verified) {
    return (
      <div className="flex justify-center items-center h-screen bg-black">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-green-500"></div>
      </div>
    );
  }

  return children;
}

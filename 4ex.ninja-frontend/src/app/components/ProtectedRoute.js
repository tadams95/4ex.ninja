"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";

export default function ProtectedRoute({ requireSubscription = true, children }) {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [verified, setVerified] = useState(false);

  useEffect(() => {
    // Wait until session loads
    if (status === "loading") return;

    if (status === "unauthenticated") {
      router.push(`/login?callbackUrl=${encodeURIComponent(window.location.href)}`);
      return;
    }

    // For subscription-protected routes:
    if (requireSubscription) {
      // Change strict check to truthy check
      if (session?.user?.isSubscribed) {
        console.log("User is subscribed, allowing access", { isSubscribed: session.user.isSubscribed });
        setVerified(true);
      } else {
        console.log("User not subscribed, redirecting to /pricing", { isSubscribed: session?.user?.isSubscribed });
        router.push("/pricing");
      }
    } else {
      setVerified(true);
    }
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

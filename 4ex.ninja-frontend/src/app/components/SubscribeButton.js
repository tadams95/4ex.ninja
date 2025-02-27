"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function SubscribeButton() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubscribe = () => {
    setLoading(true);
    // Navigate to register page instead of creating checkout session directly
    router.push("/register");
  };

  return (
    <button
      onClick={handleSubscribe}
      disabled={loading}
      className="bg-green-700 hover:bg-green-900 text-white font-bold py-2 px-4 rounded"
    >
      {loading ? "Loading..." : "Start 1-Month Free Trial"}
    </button>
  );
}

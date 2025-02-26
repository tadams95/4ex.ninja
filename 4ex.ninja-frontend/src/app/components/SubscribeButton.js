"use client";

import { useState } from "react";
import getStripe from "@/utils/get-stripe";

export default function SubscribeButton() {
  const [loading, setLoading] = useState(false);

  const handleSubscribe = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/create-checkout-session", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      // Debug logging
      console.log("Response status:", response.status);
      console.log("Response headers:", Object.fromEntries(response.headers));

      // Get response content type
      const contentType = response.headers.get("content-type");

      // Parse response based on content type
      let responseData;
      if (contentType && contentType.includes("application/json")) {
        responseData = await response.json();
      } else {
        const text = await response.text();
        console.error("Unexpected response type:", contentType);
        console.error("Response text:", text);
        throw new Error("Server returned invalid response format");
      }

      if (!response.ok) {
        throw new Error(
          responseData.error || `HTTP error! status: ${response.status}`
        );
      }

      const stripe = await getStripe();
      if (!stripe) {
        throw new Error("Stripe failed to initialize");
      }

      const { error } = await stripe.redirectToCheckout({
        sessionId: responseData.id,
      });

      if (error) {
        console.error("Stripe redirect error:", error);
        throw error;
      }
    } catch (error) {
      console.error("Checkout error:", error);
      alert(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleSubscribe}
      disabled={loading}
      className="bg-green-700 hover:bg-green-900 text-white font-bold py-2 px-4 rounded"
    >
      {loading ? "Processing..." : "Start 1-Month Free Trial"}
    </button>
  );
}

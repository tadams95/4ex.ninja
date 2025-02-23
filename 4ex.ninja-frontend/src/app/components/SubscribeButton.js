"use client";

import { useState } from "react";
// import getStripe from "../../../utils/get-stripe";

export default function SubscribeButton() {
  const [loading, setLoading] = useState(false);

//   const handleSubscribe = async () => {
//     setLoading(true);
//     try {
//       const response = await fetch("/api/create-checkout-session", {
//         method: "POST",
//         headers: {
//           "Content-Type": "application/json",
//         },
//       });

//       if (!response.ok) throw new Error("Network response was not ok");

//       const session = await response.json();
//       const stripe = await getStripe();
//       const { error } = await stripe.redirectToCheckout({
//         sessionId: session.id,
//       });

//       if (error) throw error;
//     } catch (error) {
//       console.error("Error:", error);
//     } finally {
//       setLoading(false);
//     }
//   };

  return (
    <button
      
      disabled={loading}
      className="bg-green-700 hover:bg-green-900 text-white font-bold py-2 px-4 rounded"
    >
      Subcribe
    </button>
  );
}

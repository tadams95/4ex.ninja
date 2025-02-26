"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { signIn } from "next-auth/react";

export default function SuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session_id");
  const [status, setStatus] = useState("processing");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!sessionId) {
      setStatus("error");
      setError("No session ID found");
      return;
    }

    // Verify the payment and create an account
    const verifyPaymentAndCreateAccount = async () => {
      try {
        setStatus("verifying");
        
        // Make API call to verify payment and create account
        const response = await fetch("/api/verify-subscription", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ sessionId }),
        });
        
        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.error || "Failed to verify subscription");
        }
        
        // If successful, sign in with the credentials
        setStatus("signing-in");
        const { email, password } = data;
        
        const signInResult = await signIn("credentials", {
          redirect: false,
          email,
          password,
        });
        
        if (signInResult.error) {
          throw new Error("Failed to sign in");
        }
        
        // Redirect to feed
        setStatus("success");
        router.push("/feed");
        
      } catch (error) {
        console.error("Verification error:", error);
        setStatus("error");
        setError(error.message);
      }
    };

    verifyPaymentAndCreateAccount();
  }, [sessionId, router]);

  // Display appropriate status message
  return (
    <div className="min-h-screen bg-black flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8 bg-gray-800 p-8 rounded-lg text-center">
        <h1 className="text-3xl font-bold text-white mb-6">
          {status === "error" ? "Oops!" : "Payment Successful!"}
        </h1>
        
        {status === "error" ? (
          <div className="text-red-400 mb-4">
            <p>Something went wrong: {error}</p>
            <p className="mt-4">Please contact support for assistance.</p>
          </div>
        ) : status === "success" ? (
          <p className="text-green-400">Redirecting you to your account...</p>
        ) : (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500 mx-auto"></div>
            <p className="text-gray-300 mt-4">
              {status === "processing" ? "Processing your payment..." : 
               status === "verifying" ? "Verifying your subscription..." : 
               "Setting up your account..."}
            </p>
          </>
        )}

        {status === "error" && (
          <button 
            onClick={() => router.push("/")}
            className="mt-6 px-4 py-2 bg-green-700 hover:bg-green-800 text-white rounded-md"
          >
            Return Home
          </button>
        )}
      </div>
    </div>
  );
}

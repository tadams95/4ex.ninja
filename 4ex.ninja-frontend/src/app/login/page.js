"use client";

import { useState, useEffect } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { logAuthAttempt } from "@/lib/auth-debug";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [detailedError, setDetailedError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const callbackUrl =
    typeof window !== "undefined"
      ? new URLSearchParams(window.location.search).get("callbackUrl") ||
        "/feed"
      : "/feed";

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setDetailedError("");

    if (!email || !password) {
      setError("Email and password are required");
      setLoading(false);
      return;
    }

    try {
      console.log("Auth attempt with:", { email, passwordProvided: !!password });
      logAuthAttempt({ email, password });
      
      const result = await signIn("credentials", {
        redirect: false,
        email,
        password,
        callbackUrl,
      });

      console.log("Sign in result:", result);

      if (result?.ok && !result.error) {
        console.log("Login successful, redirecting to:", result.url || callbackUrl);
        router.replace(result.url || callbackUrl);
      } else {
        console.error("Login failed:", result?.error);
        
        // Map common error codes to user-friendly messages
        switch(result?.error) {
          case "CredentialsSignin":
            setError("Invalid email or password");
            setDetailedError("The credentials you provided could not be verified");
            break;
          default:
            setError("Authentication failed");
            setDetailedError(result?.error || "Unknown error");
        }
      }
    } catch (error) {
      console.error("Login exception:", error);
      setError("An unexpected error occurred");
      setDetailedError(error.message);
    } finally {
      setLoading(false);
    }
  };

  // Add debugging information to console on component mount
  useEffect(() => {
    console.log("Login page initialized with callback URL:", callbackUrl);
  }, [callbackUrl]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-black p-4">
      <div className="max-w-md w-full space-y-8 p-8 bg-gray-800 rounded-xl">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-white">
            Sign in to your account
          </h2>
        </div>

        {error && (
          <div className="bg-red-500/20 text-red-400 p-3 rounded-md">
            <p className="font-medium">{error}</p>
            {detailedError && <p className="text-sm mt-1 text-red-300">{detailedError}</p>}
          </div>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="appearance-none rounded-t-md relative block w-full px-3 py-2 border border-gray-600 bg-gray-700 text-white placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500 focus:z-10"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="appearance-none rounded-b-md relative block w-full px-3 py-2 border border-gray-600 bg-gray-700 text-white placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500 focus:z-10"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="text-sm">
              <Link
                href="/forgot-password"
                className="font-medium text-green-500 hover:text-green-500"
              >
                Forgot your password?
              </Link>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-green-700 hover:bg-green-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
            >
              {loading ? (
                <span className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              ) : (
                "Sign in"
              )}
            </button>
          </div>
        </form>

        <div className="text-center text-sm">
          <span className="text-gray-400">Don't have an account?</span>{" "}
          <Link
            href="/register"
            className="font-medium text-green-500 hover:text-green-500"
          >
            Register
          </Link>
        </div>
      </div>
    </div>
  );
}

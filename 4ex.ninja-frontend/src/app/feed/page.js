"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import ProtectedRoute from "../components/ProtectedRoute";
import { useSession } from "next-auth/react";

function SignalsPage() {
  // const { data: session } = useSession();
  
  // // Debug subscription status at the top level
  // useEffect(() => {
  //   if (session) {
  //     // console.log("Feed page - session:", {
  //     //   email: session.user.email,
  //     //   isSubscribed: session.user.isSubscribed
  //     // });
      
  //     // Also check subscription status directly for debugging
  //     fetch("/api/subscription-status")
  //       .then(res => res.json())
  //       .then(data => {
  //         console.log("Feed page - subscription status check:", data);
  //       })
  //       .catch(err => {
  //         console.error("Error checking status:", err);
  //       });
  //   }
  // }, [session]);

  const [crossovers, setCrossovers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEmpty, setIsEmpty] = useState(false);

  useEffect(() => {
    async function fetchCrossovers() {
      try {
        setLoading(true);
        setError(null);
        setIsEmpty(false);

        const response = await fetch("/api/crossovers");

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || "Failed to fetch crossovers");
        }

        const data = await response.json();
        setCrossovers(data.crossovers || []);

        // Check if API returned isEmpty flag
        if (data.isEmpty) {
          setIsEmpty(true);
        }
      } catch (err) {
        console.error("Error fetching crossovers:", err);
        setError(
          err.message || "Failed to load crossovers. Please try again later."
        );
      } finally {
        setLoading(false);
      }
    }

    fetchCrossovers();

    // Optional: Set up polling to refresh signals periodically
    const intervalId = setInterval(fetchCrossovers, 5 * 60 * 1000); // Every 5 minutes

    return () => clearInterval(intervalId);
  }, []);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-2xl bg-black min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
          <p className="mt-2">Loading signals...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-2xl bg-black min-h-screen">
        <h1 className="text-3xl font-bold mb-6">Latest Forex Signals</h1>
        <div className="bg-red-500/20 text-red-400 p-6 rounded-md flex flex-col items-center">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-12 w-12 mb-2"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <p className="font-medium mb-2">Error loading signals</p>
          <p className="text-sm">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-red-500/30 text-red-300 rounded-md hover:bg-red-500/40 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl bg-black min-h-screen">
      <h1 className="text-3xl font-bold mb-6">Latest MA Crossover Signals</h1>

      {isEmpty || crossovers.length === 0 ? (
        <div className="bg-gray-800 rounded-lg p-8 text-center">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-16 w-16 mx-auto mb-4 text-gray-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="text-xl font-medium mb-2">No signals available</p>
          <p className="text-gray-400">
            Our system is currently analyzing market movements.
            <br />
            New MA crossover signals will appear here when they occur.
          </p>
          <p className="text-gray-500 mt-4 text-sm">
            Crossovers are monitored across multiple timeframes and pairs.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {crossovers.map((crossover, index) => (
            <motion.div
              key={crossover._id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              className={`bg-gray-700 rounded-lg p-6 shadow-lg border-l-4 ${
                crossover.crossoverType === "BULLISH" ? "border-green-500" : "border-red-500"
              }`}
            >
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">{crossover.pair}</h2>
                <span
                  className={`px-3 py-1 rounded-full text-sm ${
                    crossover.crossoverType === "BULLISH"
                      ? "bg-green-500/20 text-green-500"
                      : "bg-red-500/20 text-red-400"
                  }`}
                >
                  {crossover.crossoverType}
                </span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <p className="text-gray-300">Timeframe:</p>
                  <p className="font-medium">{crossover.timeframe}</p>
                </div>
                <div className="flex justify-between">
                  <p className="text-gray-300">Price:</p>
                  <p className="font-medium">{crossover.price}</p>
                </div>
                {/* <div className="flex justify-between">
                  <p className="text-gray-300">Fast MA:</p>
                  <p className="font-medium">{crossover.fastMA} SMA</p>
                </div>
                <div className="flex justify-between">
                  <p className="text-gray-300">Slow MA:</p>
                  <p className="font-medium">{crossover.slowMA} SMA</p>
                </div> */}
                <p className="text-sm text-gray-400 mt-4">
                  {new Date(crossover.timestamp).toLocaleString()}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}

// Wrap the component with ProtectedRoute
export default function ProtectedSignalsPage() {
  return (
    <ProtectedRoute requireSubscription={true}>
      <SignalsPage />
    </ProtectedRoute>
  );
}

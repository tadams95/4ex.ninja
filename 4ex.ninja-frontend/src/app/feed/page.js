"use client";

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

export default function SignalsPage() {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEmpty, setIsEmpty] = useState(false);

  // this is just a test

  useEffect(() => {
    async function fetchSignals() {
      try {
        setLoading(true);
        setError(null);
        setIsEmpty(false);
        
        const response = await fetch('/api/signals');
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to fetch signals');
        }
        
        const data = await response.json();
        setSignals(data.signals || []);
        
        // Check if API returned isEmpty flag
        if (data.isEmpty) {
          setIsEmpty(true);
        }
      } catch (err) {
        console.error('Error fetching signals:', err);
        setError(err.message || 'Failed to load signals. Please try again later.');
      } finally {
        setLoading(false);
      }
    }

    fetchSignals();
    
    // Optional: Set up polling to refresh signals periodically
    const intervalId = setInterval(fetchSignals, 5 * 60 * 1000); // Every 5 minutes
    
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
          <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
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
      <h1 className="text-3xl font-bold mb-6">Latest Forex Signals</h1>
      
      {isEmpty || signals.length === 0 ? (
        <div className="bg-gray-800 rounded-lg p-8 text-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto mb-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-xl font-medium mb-2">No signals available</p>
          <p className="text-gray-400">
            Our trading system is currently watching the markets.<br/>
            New signals will appear here when favorable conditions are identified.
          </p>
          <p className="text-gray-500 mt-4 text-sm">
            Signals are typically generated during active market hours.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {signals.map((signal, index) => (
            <motion.div
              key={signal._id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              className={`bg-gray-700 rounded-lg p-6 shadow-lg border-l-4 ${
                signal.type === "BUY" ? "border-green-500" : "border-red-500"
              }`}
            >
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">{signal.pair}</h2>
                <span
                  className={`px-3 py-1 rounded-full text-sm ${
                    signal.type === "BUY"
                      ? "bg-green-500/20 text-green-400"
                      : "bg-red-500/20 text-red-400"
                  }`}
                >
                  {signal.type}
                </span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <p className="text-gray-300">Timeframe:</p>
                  <p className="font-medium">{signal.timeframe}</p>
                </div>
                <div className="flex justify-between">
                  <p className="text-gray-300">Entry:</p>
                  <p className="font-medium">{signal.entry}</p>
                </div>
                <div className="flex justify-between">
                  <p className="text-gray-300">Stop Loss:</p>
                  <p className="font-medium text-red-400">{signal.stopLoss} ({signal.slPips} pips)</p>
                </div>
                <div className="flex justify-between">
                  <p className="text-gray-300">Take Profit:</p>
                  <p className="font-medium text-green-400">{signal.takeProfit} ({signal.tpPips} pips)</p>
                </div>
                <div className="flex justify-between">
                  <p className="text-gray-300">Risk/Reward:</p>
                  <p className="font-medium">{signal.riskRewardRatio}</p>
                </div>
                <p className="text-sm text-gray-400 mt-4">
                  {new Date(signal.timestamp).toLocaleString()}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}

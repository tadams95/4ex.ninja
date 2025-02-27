"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useAuth } from "@/contexts/AuthContext";
import getStripe from "@/utils/get-stripe";

export default function PricingPage() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { isAuthenticated } = useAuth();

  const features = [
    "Real-time trading signals",
    "Market analysis & insights",
    "Strategy backtesting",
    "Risk management tools",
    "24/7 support",
    "Trading community access"
  ];

  const handleSubscribe = async () => {
    setLoading(true);
    
    if (!isAuthenticated) {
      // If not logged in, redirect to register page
      router.push("/register");
      return;
    }
    
    try {
      const response = await fetch("/api/create-checkout-session", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to create checkout session");
      }

      const data = await response.json();
      
      // Redirect to Stripe checkout
      const stripe = await getStripe();
      if (!stripe) {
        throw new Error("Failed to initialize Stripe");
      }
      
      await stripe.redirectToCheckout({ sessionId: data.id });
      
    } catch (error) {
      console.error("Subscription error:", error);
      alert("There was a problem initiating your subscription. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <div className="py-16 text-center">
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          Simple, Transparent Pricing
        </h1>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto px-4">
          Access powerful forex trading tools and elevate your trading performance
        </p>
      </div>

      {/* Pricing Cards */}
      <div className="max-w-6xl mx-auto px-4 pb-24">
        <div className="grid md:grid-cols-1 gap-8">
          {/* Center the free trial card */}
          <div className="max-w-md mx-auto w-full">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="bg-gray-800 rounded-2xl p-8 border border-gray-700 relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 bg-green-600 text-xs px-3 py-1 rounded-bl-md">
                FREE TRIAL
              </div>
              
              <h3 className="text-2xl font-bold mb-2">4ex.ninja Access</h3>
              
              {/* Updated pricing display to show both trial and regular price */}
              <div className="mb-6">
                <div className="flex items-baseline">
                  <span className="text-4xl font-bold">$0</span>
                  <span className="text-gray-400 ml-2">for 30 days</span>
                </div>
                <div className="flex items-baseline mt-2">
                  <span className="text-xl text-gray-300">then $9.99</span>
                  <span className="text-gray-400 ml-2">/month</span>
                </div>
              </div>
              
              <p className="text-gray-400 mb-6">
                Try our full platform for 30 days, then continue for just $9.99/month.
                Cancel anytime during your trial to avoid being charged.
              </p>
              
              <ul className="space-y-3 mb-8">
                {features.map((feature, index) => (
                  <li key={index} className="flex items-start">
                    <svg className="w-5 h-5 text-green-500 mr-2 mt-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"></path>
                    </svg>
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
              
              <button
                onClick={handleSubscribe}
                disabled={loading}
                className="w-full bg-green-700 hover:bg-green-800 text-white py-3 rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
              >
                {loading ? (
                  <span className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
                ) : "Start Free Trial"}
              </button>
              
              <div className="text-center mt-4">
                <p className="text-sm text-gray-400">
                  Credit card required for trial. Cancel anytime.
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  Subscription automatically continues at $9.99/month after trial.
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </div>

      {/* FAQ Section - Updated to address pricing questions */}
      <div className="max-w-4xl mx-auto px-4 pb-24">
        <h2 className="text-3xl font-bold mb-8 text-center">Frequently Asked Questions</h2>
        
        <div className="space-y-6">
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-xl font-medium mb-2">How much does 4ex.ninja cost?</h3>
            <p className="text-gray-400">After your 30-day free trial, 4ex.ninja costs $9.99 per month. You can cancel anytime during your trial to avoid being charged.</p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-xl font-medium mb-2">Do I need to enter payment information for the free trial?</h3>
            <p className="text-gray-400">Yes, a valid payment method is required to start your free trial, but you won't be charged until the trial ends.</p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-xl font-medium mb-2">How do I cancel my subscription?</h3>
            <p className="text-gray-400">You can cancel your subscription anytime by going to your account settings. If you cancel during your trial period, you won't be charged.</p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-xl font-medium mb-2">Are there any contracts or commitments?</h3>
            <p className="text-gray-400">No, 4ex.ninja is a month-to-month subscription with no long-term contracts. You can cancel anytime.</p>
          </div>
        </div>
      </div>

      {/* Price Comparison - Optional section to add */}
      <div className="max-w-4xl mx-auto px-4 pb-24">
        <h2 className="text-3xl font-bold mb-8 text-center">Why Choose 4ex.ninja</h2>
        
        <div className="bg-gray-800 rounded-xl p-8">
          <div className="grid md:grid-cols-3 gap-6 text-center">
            <div>
              <div className="text-4xl font-bold text-green-500 mb-2">$9.99</div>
              <div className="text-gray-400">Per month</div>
              <div className="text-sm text-gray-500 mt-1">Flat monthly rate</div>
            </div>
            
            <div>
              <div className="text-4xl font-bold text-green-500 mb-2">$0</div>
              <div className="text-gray-400">To start</div>
              <div className="text-sm text-gray-500 mt-1">30-day free trial</div>
            </div>
            
            <div>
              <div className="text-4xl font-bold text-green-500 mb-2">$0</div>
              <div className="text-gray-400">Hidden fees</div>
              <div className="text-sm text-gray-500 mt-1">Transparent pricing</div>
            </div>
          </div>
          
          <div className="text-center mt-8">
            <p className="text-gray-400">
              Many competitors charge $50+ per month for similar features. 
              We believe in making forex trading tools accessible to everyone.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

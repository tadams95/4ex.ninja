'use client';

import { PricingErrorBoundary } from '@/components/error';
import { useAuth } from '@/contexts/AuthContext';
import getStripe from '@/utils/get-stripe';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

function PricingPageComponent() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { isAuthenticated } = useAuth();

  const features = [
    'Real-time trading signals',
    'Market analysis & insights',
    'Strategy backtesting',
    'Risk management tools',
    '24/7 support',
    'Trading community access',
  ];

  const handleSubscribe = async () => {
    setLoading(true);

    if (!isAuthenticated) {
      // If not logged in, redirect to register page
      router.push('/register');
      return;
    }

    try {
      const response = await fetch('/api/create-checkout-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create checkout session');
      }

      const data = await response.json();

      // Redirect to Stripe checkout
      const stripe = await getStripe();
      if (!stripe) {
        throw new Error('Stripe failed to initialize');
      }

      const { error } = await stripe.redirectToCheckout({
        sessionId: data.sessionId,
      });

      if (error) {
        throw new Error(error.message || 'Failed to redirect to checkout');
      }
    } catch (error) {
      console.error('Subscription error:', error);
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to start checkout process';
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h1 className="text-4xl font-bold mb-4">Choose Your Plan</h1>
            <p className="text-xl text-gray-300">
              Get access to premium forex signals and advanced trading tools
            </p>
          </motion.div>

          {/* Pricing Card */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="max-w-md mx-auto"
          >
            <div className="bg-gray-800 rounded-lg p-8 border border-gray-700 relative">
              {/* Popular Badge */}
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                <span className="bg-green-500 text-black px-4 py-1 rounded-full text-sm font-semibold">
                  Most Popular
                </span>
              </div>

              {/* Plan Details */}
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold mb-2">Premium Plan</h3>
                <div className="mb-4">
                  <span className="text-4xl font-bold">$47</span>
                  <span className="text-gray-400">/month</span>
                </div>
                <p className="text-gray-300">Everything you need to succeed in forex trading</p>
              </div>

              {/* Features */}
              <div className="mb-8">
                <ul className="space-y-4">
                  {features.map((feature, index) => (
                    <li key={index} className="flex items-center">
                      <svg
                        className="w-5 h-5 text-green-500 mr-3 flex-shrink-0"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                      <span className="text-gray-300">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* CTA Button */}
              <button
                onClick={handleSubscribe}
                disabled={loading}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-green-800 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200"
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Processing...
                  </div>
                ) : isAuthenticated ? (
                  'Subscribe Now'
                ) : (
                  'Sign Up & Subscribe'
                )}
              </button>

              <p className="text-sm text-gray-400 text-center mt-4">
                Cancel anytime. No hidden fees.
              </p>
            </div>
          </motion.div>

          {/* Additional Info */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="text-center mt-16"
          >
            <div className="max-w-2xl mx-auto">
              <h2 className="text-2xl font-bold mb-6">Why Choose 4ex.ninja?</h2>
              <div className="grid md:grid-cols-3 gap-8">
                <div>
                  <div className="text-green-500 text-3xl mb-4">⚡</div>
                  <h3 className="font-semibold mb-2">Real-time Signals</h3>
                  <p className="text-gray-400 text-sm">
                    Get instant notifications when profitable trading opportunities arise
                  </p>
                </div>
                <div>
                  <div className="text-green-500 text-3xl mb-4">📊</div>
                  <h3 className="font-semibold mb-2">Advanced Analytics</h3>
                  <p className="text-gray-400 text-sm">
                    Access sophisticated market analysis and backtesting tools
                  </p>
                </div>
                <div>
                  <div className="text-green-500 text-3xl mb-4">🛡️</div>
                  <h3 className="font-semibold mb-2">Risk Management</h3>
                  <p className="text-gray-400 text-sm">
                    Built-in risk management tools to protect your capital
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

export default function PricingPageWithBoundary() {
  return (
    <PricingErrorBoundary>
      <PricingPageComponent />
    </PricingErrorBoundary>
  );
}

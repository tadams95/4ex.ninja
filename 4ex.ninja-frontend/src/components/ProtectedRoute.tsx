'use client';

import { useAuth } from '@/contexts/AuthContext';
import { ConnectWallet } from '@coinbase/onchainkit/wallet';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireWallet?: boolean;
  redirectTo?: string;
}

export default function ProtectedRoute({
  children,
  requireWallet = true,
  redirectTo = '/',
}: ProtectedRouteProps) {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();
  const [isClient, setIsClient] = useState(false);

  // Hydration-safe client check
  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    // Only run client-side logic after hydration
    if (!isClient) return;
    
    // Don't redirect while still loading wallet connection state
    if (loading) return;

    // If wallet connection is required but user is not connected
    if (requireWallet && !isAuthenticated) {
      // For Web3 apps, we typically show a connect wallet screen rather than redirect
      // This is handled by the component render below
      return;
    }
  }, [isAuthenticated, loading, requireWallet, redirectTo, router, isClient]);

  // Show consistent loading state during SSR and initial client render
  if (!isClient || loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
          <p className="text-white">Loading market insights...</p>
        </div>
      </div>
    );
  }

  // Show connect wallet screen if wallet is required but not connected
  if (requireWallet && !isAuthenticated) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center max-w-md mx-auto"
        >
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white mb-4">Connect Your Wallet</h1>
            <p className="text-gray-400 text-lg">
              You need to connect your wallet to access the trading insights dashboard.
            </p>
          </div>

          <div className="bg-gray-900 border border-gray-700 rounded-lg p-8 mb-6">
            <div className="mb-6">
              <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-green-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">Secure Access</h2>
              <p className="text-gray-400 text-sm">
                Connect your wallet to securely access your personalized trading dashboard.
              </p>
            </div>

            <div className="space-y-4">
              <ConnectWallet text="Connect Wallet to Continue" className="w-full" />

              <div className="text-xs text-gray-500 space-y-1">
                <p>• Your wallet address is used for authentication</p>
                <p>• No transactions will be made without your consent</p>
                <p>• Disconnect anytime from your wallet</p>
              </div>
            </div>
          </div>

          <div className="flex justify-center space-x-4 text-sm">
            <button
              onClick={() => router.push('/')}
              className="text-gray-400 hover:text-white transition-colors"
            >
              ← Back to Home
            </button>
            <button
              onClick={() => router.push('/about')}
              className="text-gray-400 hover:text-white transition-colors"
            >
              Learn More
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  // Render the protected content if authenticated
  return <>{children}</>;
}

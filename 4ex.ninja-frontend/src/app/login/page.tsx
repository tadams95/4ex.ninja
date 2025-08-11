'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function LoginRedirect() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to home page after a brief delay
    const timer = setTimeout(() => {
      router.push('/');
    }, 3000);

    return () => clearTimeout(timer);
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-gray-900 rounded-lg p-8 text-center">
        <h1 className="text-2xl font-bold text-white mb-4">Authentication Updated</h1>

        <div className="space-y-4">
          <p className="text-gray-300">
            We've upgraded to wallet-based authentication for a better Web3 experience.
          </p>

          <div className="bg-blue-900/20 border border-blue-500/30 rounded p-4">
            <p className="text-blue-400 text-sm">
              <strong>New:</strong> Simply connect your wallet in the header to access all features.
            </p>
          </div>

          <div className="space-y-3">
            <p className="text-gray-400 text-sm">Connect with:</p>
            <div className="flex justify-center space-x-4 text-sm">
              <span className="text-blue-400">• Coinbase Wallet</span>
              <span className="text-orange-400">• MetaMask</span>
              <span className="text-purple-400">• WalletConnect</span>
            </div>
          </div>

          <Link
            href="/"
            className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md font-medium transition-colors"
          >
            Go to Homepage
          </Link>

          <p className="text-gray-500 text-xs mt-4">Redirecting automatically in 3 seconds...</p>
        </div>
      </div>
    </div>
  );
}

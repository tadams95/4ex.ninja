'use client';

import { WalletProfile } from '@/components/WalletConnection';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useAccount } from 'wagmi';

export default function WelcomeBanner() {
  const { isConnected, address } = useAccount();
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  if (!isHydrated || !isConnected) {
    return null;
  }

  return (
    <div className="bg-gradient-to-r from-green-900/20 to-green-800/20 border border-green-700/30 rounded-xl p-6 mb-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse" />
            <span className="text-green-400 font-medium">Connected</span>
          </div>
          <WalletProfile size="md" />
        </div>

        <div className="flex space-x-3">
          <Link
            href="/feed"
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            View Signals
          </Link>
          <Link
            href="/account"
            className="border border-green-600 text-green-400 hover:bg-green-600/10 px-4 py-2 rounded-lg font-medium transition-colors"
          >
            Account
          </Link>
        </div>
      </div>

      <div className="mt-4 text-gray-300">
        <p className="text-sm">
          Welcome back! You can now access premium forex signals and manage your trading strategy.
        </p>
      </div>
    </div>
  );
}

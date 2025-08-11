'use client';

import { Avatar, Identity, Name } from '@coinbase/onchainkit/identity';
import {
  Wallet,
  WalletDropdown,
  WalletDropdownDisconnect,
  WalletDropdownLink,
} from '@coinbase/onchainkit/wallet';
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
          <Wallet>
            <WalletDropdown>
              <div className="flex items-center space-x-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors cursor-pointer group px-3 py-2 text-sm">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <Identity
                  address={address}
                  schemaId="0xf8b05c79f090979bf4a80270aba232dff11a10d9ca55c4f88de95317970f0de9"
                >
                  <Avatar className="w-6 h-6" />
                  <Name className="text-white font-medium" />
                </Identity>
                <svg
                  className="w-4 h-4 text-gray-400 group-hover:text-gray-300 transition-colors"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </div>
              <WalletDropdownLink
                icon="wallet"
                href="https://wallet.coinbase.com"
                target="_blank"
                rel="noopener noreferrer"
              >
                Open Wallet
              </WalletDropdownLink>
              <WalletDropdownLink icon="user" href="/account">
                Account Settings
              </WalletDropdownLink>
              <WalletDropdownDisconnect />
            </WalletDropdown>
          </Wallet>
        </div>

        <div className="flex space-x-3">
          <Link
            href="/feed"
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            View Signals
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

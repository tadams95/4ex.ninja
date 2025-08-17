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
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse" />
            <span className="text-green-400 font-medium">Connected</span>
          </div>
          <Wallet>
            <WalletDropdown>
              <div
                className="flex items-center space-x-3 bg-gray-800 hover:bg-gray-700/80 
                rounded-lg transition-all duration-200 cursor-pointer group px-3 py-2 text-sm
                min-h-[44px] focus-within:ring-2 focus-within:ring-green-500/50"
              >
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <Identity
                  address={address}
                  schemaId="0xf8b05c79f090979bf4a80270aba232dff11a10d9ca55c4f88de95317970f0de9"
                  className="flex items-center space-x-2"
                >
                  <Avatar
                    className="w-6 h-6 transition-all duration-200 group-hover:scale-105"
                    aria-hidden="true"
                  />
                  <Name
                    className="text-white font-medium group-hover:text-green-100"
                    aria-label="Connected wallet name"
                  />
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
                className="flex items-center px-4 py-3 hover:bg-neutral-800/50 
                  transition-all duration-200 group min-h-[44px] rounded-md mx-2 my-1
                  focus:outline-none focus:ring-2 focus:ring-green-500/50"
                icon="wallet"
                href="https://wallet.coinbase.com"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Open Coinbase Wallet in new tab"
              >
                Open Wallet
              </WalletDropdownLink>
              <WalletDropdownLink
                className="flex items-center px-4 py-3 hover:bg-neutral-800/50 
                  transition-all duration-200 group min-h-[44px] rounded-md mx-2 my-1
                  focus:outline-none focus:ring-2 focus:ring-green-500/50"
                icon="user"
                href="/account"
                aria-label="Go to account settings"
              >
                Account Settings
              </WalletDropdownLink>
              <WalletDropdownDisconnect
                className="mx-2 my-1 hover:bg-red-500/10 hover:text-red-300 
                  transition-all duration-200 min-h-[44px] rounded-md
                  focus:outline-none focus:ring-2 focus:ring-red-500/50"
                aria-label="Disconnect wallet"
              />
            </WalletDropdown>
          </Wallet>
        </div>

        <div className="flex space-x-4">
          <Link
            href="/insights"
            className="bg-green-700 hover:bg-green-800 active:bg-green-900
              text-white border border-green-600 hover:border-green-500 
              hover:text-green-100 font-semibold rounded-xl 
              transition-all duration-300 ease-out px-4 py-2.5 text-sm 
              cursor-pointer outline-none hover:shadow-lg 
              hover:shadow-green-500/25 hover:scale-[1.02] active:scale-[0.98]
              focus-visible:ring-2 focus-visible:ring-green-500 
              focus-visible:ring-offset-2 focus-visible:ring-offset-green-900/20
              min-h-[44px] flex items-center justify-center"
            aria-label="View trading insights dashboard"
          >
            View Dashboard
          </Link>
        </div>
      </div>

      {/* <div className="mt-4 text-gray-300">
        <p className="text-sm">
          Welcome back! You can now access premium forex signals and manage your trading strategy.
        </p>
      </div> */}
    </div>
  );
}

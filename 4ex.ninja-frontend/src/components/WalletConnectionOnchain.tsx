'use client';

import { Avatar, Identity, Name } from '@coinbase/onchainkit/identity';
import {
  ConnectWallet,
  Wallet,
  WalletDropdown,
  WalletDropdownDisconnect,
  WalletDropdownLink,
} from '@coinbase/onchainkit/wallet';
import { useEffect, useState } from 'react';
import { useAccount, useDisconnect } from 'wagmi';

export default function WalletConnectionOnchain() {
  const { address, isConnected } = useAccount();
  const { disconnect } = useDisconnect();
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  // Show loading state during hydration to prevent mismatch
  if (!isHydrated) {
    return <div className="bg-gray-700 animate-pulse rounded-lg px-6 py-3 w-32 h-12"></div>;
  }

  return (
    <div className="flex items-center">
      {!isConnected ? (
        <Wallet>
          <ConnectWallet>
            <button className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors cursor-pointer border-0 outline-none shadow-lg hover:shadow-xl">
              Connect Wallet
            </button>
          </ConnectWallet>
        </Wallet>
      ) : (
        <div className="flex items-center space-x-3">
          <Wallet>
            <WalletDropdown>
              <div className="flex items-center space-x-2 bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded-lg transition-colors cursor-pointer">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <Identity
                  address={address}
                  schemaId="0xf8b05c79f090979bf4a80270aba232dff11a10d9ca55c4f88de95317970f0de9"
                >
                  <Avatar className="w-6 h-6" />
                  <Name className="text-sm font-medium text-white" />
                </Identity>
                <svg
                  className="w-4 h-4 text-gray-400"
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
              <WalletDropdownDisconnect />
            </WalletDropdown>
          </Wallet>

          {/* Alternative disconnect button */}
          <button
            onClick={() => disconnect()}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium transition-colors cursor-pointer border-0 outline-none text-sm"
            title="Disconnect Wallet"
          >
            Disconnect
          </button>
        </div>
      )}
    </div>
  );
}

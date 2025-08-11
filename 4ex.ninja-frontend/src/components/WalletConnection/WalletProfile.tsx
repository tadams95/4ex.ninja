'use client';

import { Avatar, Identity, Name } from '@coinbase/onchainkit/identity';
import {
  Wallet,
  WalletDropdown,
  WalletDropdownDisconnect,
  WalletDropdownLink,
} from '@coinbase/onchainkit/wallet';
import { useEffect, useState } from 'react';
import { useAccount } from 'wagmi';

interface WalletProfileProps {
  size?: 'sm' | 'md' | 'lg';
  showBalance?: boolean;
  className?: string;
}

export default function WalletProfile({
  size = 'md',
  showBalance = false,
  className = '',
}: WalletProfileProps) {
  const { address, isConnected } = useAccount();
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  // Size variants
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-3 text-base',
  };

  const avatarSizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  const dotSizes = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-2.5 h-2.5',
  };

  // Show loading state during hydration
  if (!isHydrated || !isConnected) {
    return null;
  }

  return (
    <Wallet>
      <WalletDropdown>
        <div
          className={`
          flex items-center space-x-2 bg-gray-800 hover:bg-gray-700 
          rounded-lg transition-colors cursor-pointer group
          ${sizeClasses[size]} ${className}
        `}
        >
          {/* Connection indicator */}
          <div
            className={`
            bg-green-400 rounded-full animate-pulse
            ${dotSizes[size]}
          `}
          />

          <Identity
            address={address}
            schemaId="0xf8b05c79f090979bf4a80270aba232dff11a10d9ca55c4f88de95317970f0de9"
          >
            <Avatar className={avatarSizes[size]} />
            <Name className="text-white font-medium" />
          </Identity>

          {/* Dropdown arrow */}
          <svg
            className="w-4 h-4 text-gray-400 group-hover:text-gray-300 transition-colors"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>

        {/* Dropdown content */}
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
  );
}

'use client';

import { ConnectWallet, Wallet } from '@coinbase/onchainkit/wallet';
import { useEffect, useState } from 'react';
import { useAccount } from 'wagmi';

interface WalletButtonProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'primary' | 'secondary' | 'outline';
  className?: string;
}

export default function WalletButton({
  size = 'md',
  variant = 'primary',
  className = '',
}: WalletButtonProps) {
  const { isConnected } = useAccount();
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  // Size variants
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  // Variant styles to match app's color scheme
  const variantClasses = {
    primary: 'bg-green-600 hover:bg-green-700 text-white border-green-600 hover:border-green-700',
    secondary: 'bg-gray-700 hover:bg-gray-600 text-white border-gray-700 hover:border-gray-600',
    outline:
      'bg-transparent hover:bg-green-600/10 text-green-400 border-green-400 hover:text-green-300 hover:border-green-300',
  };

  const baseClasses = `
    font-semibold rounded-lg transition-all duration-200 
    border cursor-pointer outline-none
    hover:shadow-lg hover:scale-[1.02] active:scale-[0.98]
    disabled:opacity-50 disabled:cursor-not-allowed
  `.trim();

  // Show loading state during hydration
  if (!isHydrated) {
    return (
      <div
        className={`
        bg-gray-700 animate-pulse rounded-lg 
        ${sizeClasses[size]} 
        ${className}
      `}
      >
        <span className="opacity-0">Connect Wallet</span>
      </div>
    );
  }

  // Don't show if already connected
  if (isConnected) return null;

  return (
    <Wallet>
      <ConnectWallet>
        <button
          className={`
            ${baseClasses} 
            ${sizeClasses[size]} 
            ${variantClasses[variant]} 
            ${className}
          `}
        >
          Connect Wallet
        </button>
      </ConnectWallet>
    </Wallet>
  );
}

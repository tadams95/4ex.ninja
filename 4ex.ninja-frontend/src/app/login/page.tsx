'use client';

import { ConnectWallet } from '@coinbase/onchainkit/wallet';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect } from 'react';
import { useAccount } from 'wagmi';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isConnected } = useAccount();
  const callbackUrl = searchParams.get('callbackUrl') || '/';

  useEffect(() => {
    if (isConnected) {
      // User is connected, redirect to callback URL
      router.push(callbackUrl);
    }
  }, [isConnected, router, callbackUrl]);

  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center">
      <div className="max-w-md w-full mx-auto p-6">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-4">Connect Your Wallet</h1>
          <p className="text-neutral-400 mb-6">
            Connect your wallet to access premium signals and features.
          </p>
        </div>

        <div className="flex justify-center mb-6">
          <ConnectWallet />
        </div>

        <div className="text-center">
          <p className="text-sm text-neutral-500">
            By connecting your wallet, you agree to our terms of service.
          </p>
        </div>
      </div>
    </div>
  );
}

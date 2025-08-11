/**
 * Simple Wallet Connection Hook
 *
 * Provides basic wallet connection functionality without WebSocket complexity
 */

import { walletService, type WalletConnectionState } from '@/utils/onchain-notification-manager';
import { useCallback, useEffect, useState } from 'react';

// Simple wallet connection hook
export function useWallet() {
  const [walletState, setWalletState] = useState<WalletConnectionState>({ isConnected: false });
  const [isConnecting, setIsConnecting] = useState(false);

  // Subscribe to wallet state changes
  useEffect(() => {
    const unsubscribe = walletService.subscribe(setWalletState);
    return unsubscribe;
  }, []);

  // Connect wallet via browser wallet popup
  const connectWallet = useCallback(async () => {
    setIsConnecting(true);
    try {
      const success = await walletService.connectWallet();
      return success;
    } finally {
      setIsConnecting(false);
    }
  }, []);

  // Disconnect wallet
  const disconnectWallet = useCallback(() => {
    walletService.disconnect();
  }, []);

  // Get available wallets
  const getAvailableWallets = useCallback(() => {
    return walletService.getAvailableWallets();
  }, []);

  return {
    walletState,
    isConnecting,
    connectWallet,
    disconnectWallet,
    getAvailableWallets,
  };
}

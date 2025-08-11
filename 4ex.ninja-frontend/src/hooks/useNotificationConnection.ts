/**
 * Simple Wallet Connection Hook
 * 
 * Provides basic wallet connection functionality without WebSocket complexity
 */

import { useState, useEffect, useCallback } from 'react';
import { 
  walletService, 
  type WalletConnectionState,
  type AccessTier 
} from '@/utils/onchain-notification-manager';

// Simple wallet connection hook
export function useWallet() {
  const [walletState, setWalletState] = useState<WalletConnectionState>({ isConnected: false });
  const [isConnecting, setIsConnecting] = useState(false);

  // Subscribe to wallet state changes
  useEffect(() => {
    const unsubscribe = walletService.subscribe(setWalletState);
    return unsubscribe;
  }, []);

  // Connect wallet
  const connectWallet = useCallback(async (address: string) => {
    setIsConnecting(true);
    try {
      const success = await walletService.connectWallet(address);
      return success;
    } finally {
      setIsConnecting(false);
    }
  }, []);

  // Disconnect wallet
  const disconnectWallet = useCallback(() => {
    walletService.disconnect();
  }, []);

  return {
    walletState,
    isConnecting,
    connectWallet,
    disconnectWallet,
  };
}

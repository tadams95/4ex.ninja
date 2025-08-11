/**
 * Simplified Onchain Wallet Service
 *
 * Provides basic wallet connection and token balance checking
 * without the complexity of WebSocket integration
 */

import { createPublicClient, http } from 'viem';
import { base } from 'viem/chains';

// Types
export type AccessTier = 'public' | 'holders' | 'premium' | 'whale';

export interface WalletConnectionState {
  isConnected: boolean;
  address?: string;
  tokenBalance?: bigint;
  accessTier?: AccessTier;
  isConnecting?: boolean;
  error?: string;
}

// Constants for real token integration
export const TOKEN_CONFIG = {
  // Placeholder - will be updated when $4EX token is deployed
  ADDRESS: '0x0000000000000000000000000000000000000000' as const,
  DECIMALS: 18,
  SYMBOL: '4EX',
};

// Token thresholds for access tiers
export const ACCESS_THRESHOLDS = {
  holders: BigInt(1000 * Math.pow(10, TOKEN_CONFIG.DECIMALS)), // 1,000 $4EX
  premium: BigInt(10000 * Math.pow(10, TOKEN_CONFIG.DECIMALS)), // 10,000 $4EX
  whale: BigInt(100000 * Math.pow(10, TOKEN_CONFIG.DECIMALS)), // 100,000 $4EX
} as const;

// ERC20 ABI for token balance checking
const ERC20_ABI = [
  {
    inputs: [{ name: 'account', type: 'address' }],
    name: 'balanceOf',
    outputs: [{ name: '', type: 'uint256' }],
    stateMutability: 'view',
    type: 'function',
  },
] as const;

class SimpleWalletService {
  private client: any;
  private connectionState: WalletConnectionState = {
    isConnected: false,
  };
  private listeners: Set<(state: WalletConnectionState) => void> = new Set();

  constructor() {
    this.initializeClient();
  }

  private initializeClient() {
    try {
      // Initialize Viem client for Base network
      this.client = createPublicClient({
        chain: base,
        transport: http(),
      });
    } catch (error) {
      console.error('Failed to initialize onchain client:', error);
    }
  }

  /**
   * Connect wallet and get token balance
   */
  public async connectWallet(walletAddress: string): Promise<boolean> {
    try {
      this.updateConnectionState({ isConnecting: true });

      // Validate wallet address
      if (!this.isValidAddress(walletAddress)) {
        throw new Error('Invalid wallet address');
      }

      // Get token balance (real or simulated)
      const tokenBalance = await this.getTokenBalance(walletAddress);
      const accessTier = this.calculateAccessTier(tokenBalance);

      // Update connection state
      this.updateConnectionState({
        isConnected: true,
        address: walletAddress,
        tokenBalance,
        accessTier,
        isConnecting: false,
        error: undefined,
      });

      return true;
    } catch (error) {
      console.error('Wallet connection failed:', error);
      this.updateConnectionState({
        isConnected: false,
        isConnecting: false,
        error: error instanceof Error ? error.message : 'Connection failed',
      });
      return false;
    }
  }

  /**
   * Get token balance - real or simulated
   */
  private async getTokenBalance(walletAddress: string): Promise<bigint> {
    try {
      // Skip if token not deployed yet
      if (TOKEN_CONFIG.ADDRESS === '0x0000000000000000000000000000000000000000') {
        // Fallback to simulation until token is deployed
        return this.getSimulatedBalance(walletAddress);
      }

      // Real onchain balance check would go here
      // For now, fall back to simulation
      return this.getSimulatedBalance(walletAddress);
    } catch (error) {
      console.error('Failed to get token balance:', error);
      return this.getSimulatedBalance(walletAddress);
    }
  }

  /**
   * Temporary simulation for testing
   */
  private getSimulatedBalance(walletAddress: string): bigint {
    const lastChar = walletAddress.slice(-1);
    switch (lastChar) {
      case '0':
        return ACCESS_THRESHOLDS.whale + BigInt(1); // Whale tier
      case '1':
        return ACCESS_THRESHOLDS.premium + BigInt(1); // Premium tier
      case '2':
        return ACCESS_THRESHOLDS.holders + BigInt(1); // Holders tier
      default:
        return BigInt(0); // Free tier
    }
  }

  /**
   * Calculate access tier based on token balance
   */
  private calculateAccessTier(balance: bigint): AccessTier {
    if (balance >= ACCESS_THRESHOLDS.whale) return 'whale';
    if (balance >= ACCESS_THRESHOLDS.premium) return 'premium';
    if (balance >= ACCESS_THRESHOLDS.holders) return 'holders';
    return 'public';
  }

  /**
   * Disconnect wallet
   */
  public disconnect(): void {
    this.updateConnectionState({
      isConnected: false,
      address: undefined,
      tokenBalance: undefined,
      accessTier: undefined,
      isConnecting: false,
      error: undefined,
    });
  }

  /**
   * Subscribe to connection state changes
   */
  public subscribe(listener: (state: WalletConnectionState) => void): () => void {
    this.listeners.add(listener);
    // Send current state immediately
    listener(this.connectionState);

    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Get current connection state
   */
  public getConnectionState(): WalletConnectionState {
    return { ...this.connectionState };
  }

  /**
   * Validate Ethereum address format
   */
  private isValidAddress(address: string): boolean {
    return /^0x[a-fA-F0-9]{40}$/.test(address);
  }

  /**
   * Update connection state and notify listeners
   */
  private updateConnectionState(newState: Partial<WalletConnectionState>): void {
    this.connectionState = { ...this.connectionState, ...newState };
    this.listeners.forEach(listener => listener(this.connectionState));
  }

  /**
   * Update token contract address (when $4EX token is deployed)
   */
  public updateTokenAddress(address: string): void {
    if (this.isValidAddress(address)) {
      (TOKEN_CONFIG as any).ADDRESS = address;
      console.log(`Token address updated to: ${address}`);

      // Refresh balance if connected
      if (this.connectionState.isConnected && this.connectionState.address) {
        this.connectWallet(this.connectionState.address);
      }
    }
  }
}

// Export singleton instance
export const walletService = new SimpleWalletService();

// Export utility functions
export function formatTokenBalance(
  balance: bigint,
  decimals: number = TOKEN_CONFIG.DECIMALS
): string {
  const divisor = BigInt(Math.pow(10, decimals));
  const wholePart = balance / divisor;
  const fractionalPart = balance % divisor;

  if (fractionalPart === BigInt(0)) {
    return wholePart.toString();
  }

  const fractionalStr = fractionalPart.toString().padStart(decimals, '0');
  const trimmedFractional = fractionalStr.replace(/0+$/, '');

  return trimmedFractional ? `${wholePart}.${trimmedFractional}` : wholePart.toString();
}

export function getAccessTierLabel(tier: AccessTier): string {
  switch (tier) {
    case 'whale':
      return 'Whale (100,000+ $4EX)';
    case 'premium':
      return 'Premium (10,000+ $4EX)';
    case 'holders':
      return 'Holder (1,000+ $4EX)';
    case 'public':
      return 'Public (0 $4EX)';
    default:
      return 'Unknown';
  }
}

export function getAccessTierColor(tier: AccessTier): string {
  switch (tier) {
    case 'whale':
      return 'text-purple-400';
    case 'premium':
      return 'text-yellow-400';
    case 'holders':
      return 'text-blue-400';
    case 'public':
      return 'text-gray-400';
    default:
      return 'text-gray-400';
  }
}

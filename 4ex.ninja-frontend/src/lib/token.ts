/**
 * 4EX Token Configuration
 *
 * Contract deployed via streme.fun on Base network
 */

// 4EX Token Contract on Base
export const TOKEN_CONFIG = {
  address: '0x3Aa87C18d7080484e4839afA3540e520452ccA3E' as const,
  symbol: '4EX' as const,
  name: '4EX' as const,
  decimals: 18 as const,
  chainId: 8453 as const, // Base mainnet
} as const;

// Token tier thresholds (in wei, 18 decimals)
export const TOKEN_TIERS = {
  FREE: BigInt(0),
  HOLDERS: BigInt(1000) * BigInt(10) ** BigInt(18), // 1,000 4EX
  PREMIUM: BigInt(10000) * BigInt(10) ** BigInt(18), // 10,000 4EX
  WHALE: BigInt(100000) * BigInt(10) ** BigInt(18), // 100,000 4EX
} as const;

export type AccessTier = 'public' | 'holders' | 'premium' | 'whale';

/**
 * Calculate access tier based on token balance
 */
export function calculateAccessTier(balance: bigint): AccessTier {
  if (balance >= TOKEN_TIERS.WHALE) return 'whale';
  if (balance >= TOKEN_TIERS.PREMIUM) return 'premium';
  if (balance >= TOKEN_TIERS.HOLDERS) return 'holders';
  return 'public';
}

/**
 * Get notification channels for access tier
 */
export function getNotificationChannels(tier: AccessTier): string[] {
  const channels = {
    public: [],
    holders: ['premium_signals'],
    premium: ['premium_signals', 'whale_signals'],
    whale: ['premium_signals', 'whale_signals', 'alpha_signals'],
  };

  return channels[tier] || [];
}

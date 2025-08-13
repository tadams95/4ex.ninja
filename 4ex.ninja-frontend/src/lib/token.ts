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

// Token tier thresholds (in wei, 18 decimals) - Following official TierStructure.md
export const TOKEN_TIERS = {
  PUBLIC: BigInt(0), // 0 tokens - No access
  HOLDER: BigInt(1) * BigInt(10) ** BigInt(18), // 1 4EX - Holder tier
  BASIC: BigInt(1000000) * BigInt(10) ** BigInt(18), // 1,000,000 4EX - Basic tier
  PREMIUM: BigInt(10000000) * BigInt(10) ** BigInt(18), // 10,000,000 4EX - Premium tier
  WHALE: BigInt(100000000) * BigInt(10) ** BigInt(18), // 100,000,000 4EX - Whale tier
} as const;

export type AccessTier = 'public' | 'holder' | 'basic' | 'premium' | 'whale';

/**
 * Calculate access tier based on token balance
 * Follows official tier structure: 1 token = holder, 1M = basic, 10M = premium, 100M = whale
 */
export function calculateAccessTier(balance: bigint): AccessTier {
  if (balance >= TOKEN_TIERS.WHALE) return 'whale'; // 100M+ tokens
  if (balance >= TOKEN_TIERS.PREMIUM) return 'premium'; // 10M+ tokens
  if (balance >= TOKEN_TIERS.BASIC) return 'basic'; // 1M+ tokens
  if (balance >= TOKEN_TIERS.HOLDER) return 'holder'; // 1+ tokens
  return 'public'; // 0 tokens
}

/**
 * Get notification channels for access tier
 */
export function getNotificationChannels(tier: AccessTier): string[] {
  const channels = {
    public: [],
    holder: ['basic_signals'],
    basic: ['basic_signals', 'premium_signals'],
    premium: ['basic_signals', 'premium_signals'],
    whale: ['basic_signals', 'premium_signals', 'whale_signals'],
  };

  return channels[tier] || [];
}

'use client';

import { WalletButton } from '@/components/WalletConnection';
import { useTokenBalance } from '@/hooks/useTokenBalanceSimple';
import { getNotificationChannels } from '@/lib/token';
import { useAccount } from 'wagmi';

// Format token amount for display
function formatTokenAmount(amount: bigint): string {
  const formatted = Number(amount) / 10 ** 18;
  if (formatted >= 1000000) {
    return `${(formatted / 1000000).toFixed(1)}M`;
  }
  if (formatted >= 1000) {
    return `${(formatted / 1000).toFixed(1)}K`;
  }
  return formatted.toFixed(2);
}

// Get tier benefits
function getTierBenefits(tier: string): string[] {
  switch (tier) {
    case 'whale':
      return ['Premium Signals', 'Whale Signals', 'Alpha Signals', 'Priority Support'];
    case 'premium':
      return ['Premium Signals', 'Whale Signals', 'Enhanced Analytics'];
    case 'holders':
      return ['Premium Signals', 'Basic Analytics'];
    default:
      return ['Basic Signals Only'];
  }
}

// Get next tier requirements
function getNextTierInfo(tier: string): { name: string; requirement: string } | null {
  switch (tier) {
    case 'public':
      return { name: 'Holders', requirement: '1,000 $4EX tokens' };
    case 'holders':
      return { name: 'Premium', requirement: '10,000 $4EX tokens' };
    case 'premium':
      return { name: 'Whale', requirement: '100,000 $4EX tokens' };
    default:
      return null;
  }
}

export default function TokenTierDashboard() {
  const { isConnected } = useAccount();
  const { balance, tier, isLoading } = useTokenBalance();

  // Show wallet connection prompt if not connected
  if (!isConnected) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 max-w-md mx-auto">
        <h3 className="text-xl font-semibold text-white mb-4">Connect Wallet to View Your Tier</h3>
        <p className="text-gray-300 mb-6">
          Connect your wallet to see your $4EX token balance and access tier benefits.
        </p>
        <WalletButton variant="primary" className="w-full" />
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 max-w-md mx-auto animate-pulse">
        <div className="h-6 bg-gray-700 rounded mb-4"></div>
        <div className="h-4 bg-gray-700 rounded mb-2"></div>
        <div className="h-4 bg-gray-700 rounded mb-6"></div>
        <div className="h-20 bg-gray-700 rounded"></div>
      </div>
    );
  }

  const tierColors = {
    public: 'text-gray-400 border-gray-600',
    holders: 'text-green-400 border-green-600',
    premium: 'text-blue-400 border-blue-600',
    whale: 'text-purple-400 border-purple-600',
  };

  const tierBadgeColors = {
    public: 'bg-gray-600 text-gray-100',
    holders: 'bg-green-600 text-green-100',
    premium: 'bg-blue-600 text-blue-100',
    whale: 'bg-purple-600 text-purple-100',
  };

  const benefits = getTierBenefits(tier);
  const nextTier = getNextTierInfo(tier);
  const channels = getNotificationChannels(tier);

  return (
    <div className={`bg-gray-900 border rounded-lg p-6 max-w-md mx-auto ${tierColors[tier]}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-semibold text-white">Your Access Tier</h3>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${tierBadgeColors[tier]}`}>
          {tier.charAt(0).toUpperCase() + tier.slice(1)}
        </span>
      </div>

      {/* Token Balance */}
      <div className="mb-6">
        <p className="text-gray-300 text-sm mb-1">$4EX Token Balance</p>
        <p className="text-2xl font-bold text-white">{formatTokenAmount(balance)} $4EX</p>
      </div>

      {/* Current Benefits */}
      <div className="mb-6">
        <h4 className="text-white font-medium mb-3">Your Benefits</h4>
        <ul className="space-y-2">
          {benefits.map((benefit, index) => (
            <li key={index} className="flex items-center text-sm">
              <span className="w-2 h-2 bg-green-400 rounded-full mr-3"></span>
              <span className="text-gray-300">{benefit}</span>
            </li>
          ))}
        </ul>
        {channels.length > 0 && (
          <p className="text-xs text-gray-400 mt-2">
            Active Discord channels: {channels.join(', ')}
          </p>
        )}
      </div>

      {/* Next Tier Info */}
      {nextTier && (
        <div className="bg-gray-800 rounded-lg p-4">
          <h4 className="text-white font-medium mb-2">Upgrade to {nextTier.name}</h4>
          <p className="text-gray-300 text-sm mb-3">Get access to more signals and features</p>
          <p className="text-xs text-gray-400">Requirement: {nextTier.requirement}</p>
        </div>
      )}
    </div>
  );
}

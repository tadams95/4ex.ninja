'use client';

import { TOKEN_CONFIG } from '@/lib/token';
import { SwapDefault } from '@coinbase/onchainkit/swap';
import type { Token } from '@coinbase/onchainkit/token';

const eth: Token = {
  name: 'ETH',
  address: '',
  symbol: 'ETH',
  decimals: 18,
  image: 'https://wallet-api-production.s3.amazonaws.com/uploads/tokens/eth_288.png',
  chainId: 8453,
};

const usdc: Token = {
  name: 'USDC',
  address: '0x833589fcd6edb6e08f4c7c32d4f71b54bda02913',
  symbol: 'USDC',
  decimals: 6,
  image:
    'https://d3r81g40ycuhqg.cloudfront.net/wallet/wais/44/2b/442b80bd16af0c0d9b22e03a16753823fe826e5bfd457292b55fa0ba8c1ba213-ZWUzYjJmZGUtMDYxNy00NDcyLTg0NjQtMWI4OGEwYjBiODE2',
  chainId: 8453,
};

const fourExToken: Token = {
  address: TOKEN_CONFIG.address as `0x${string}`,
  chainId: TOKEN_CONFIG.chainId,
  decimals: TOKEN_CONFIG.decimals,
  name: TOKEN_CONFIG.name,
  symbol: TOKEN_CONFIG.symbol,
  image: '/4EX.png',
};

export default function SwapPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      <div className="container mx-auto px-4 py-12 lg:py-20">
        <div className="max-w-4xl mx-auto">
          {/* Hero Section */}
          <div className="text-center mb-16">
            <div className="inline-block mb-6">
              <div className="bg-gray-800 border border-gray-700 rounded-full px-6 py-2 text-sm font-medium text-blue-500">
                ⚡ Powered by Base
              </div>
            </div>

            <h1 className="text-5xl lg:text-7xl font-bold mb-6 leading-tight">
              <span className="text-white">Swap for</span>
              <br />
              <span className="text-green-400">$4EX</span>
            </h1>

            <p className="text-xl lg:text-2xl text-gray-400 max-w-3xl mx-auto leading-relaxed">
              Seamlessly upgrade your account tier with instant token swaps.
              <span className="block mt-2 text-lg text-gray-500">
                Connect your wallet and choose from your available tokens.
              </span>
            </p>
          </div>

          {/* Simplified Swap Interface */}
          <div className="flex justify-center">
            <div className="w-full max-w-md">
              <SwapDefault from={[eth, usdc]} to={[fourExToken]} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

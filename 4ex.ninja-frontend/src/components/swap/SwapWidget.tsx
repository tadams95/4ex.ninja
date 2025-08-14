'use client';

import { TOKEN_CONFIG } from '@/lib/token';
import { Swap, SwapAmountInput, SwapToggleButton } from '@coinbase/onchainkit/swap';
import { Token } from '@coinbase/onchainkit/token';

const fourExToken: Token = {
  address: TOKEN_CONFIG.address as `0x${string}`,
  chainId: TOKEN_CONFIG.chainId,
  decimals: TOKEN_CONFIG.decimals,
  name: TOKEN_CONFIG.name,
  symbol: TOKEN_CONFIG.symbol,
  image: '', // Add logo URL if available
};

export default function SwapWidget() {
  return (
    <div className="w-full max-w-lg mx-auto">
      <Swap>
        <SwapAmountInput
          label="Sell"
          type="from"
          token={undefined} // Let user choose
        />
        <SwapToggleButton />
        <SwapAmountInput
          label="Buy"
          type="to"
          token={fourExToken} // Default to $4EX
        />
      </Swap>
    </div>
  );
}

'use client';

import { Avatar, Identity, Name } from '@coinbase/onchainkit/identity';
import {
  ConnectWallet,
  Wallet,
  WalletDropdown,
  WalletDropdownDisconnect,
  WalletDropdownLink,
} from '@coinbase/onchainkit/wallet';
import { useAccount } from 'wagmi';

export default function WalletConnectionOnchain() {
  const { address, isConnected } = useAccount();

  return (
    <div className="flex items-center">
      {!isConnected ? (
        <Wallet>
          <ConnectWallet>
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors cursor-pointer border-0 outline-none">
              Connect Wallet
            </button>
          </ConnectWallet>
        </Wallet>
      ) : (
        <Wallet>
          <WalletDropdown>
            <div className="flex items-center space-x-2 bg-gray-800 hover:bg-gray-700 px-3 py-2 rounded-md transition-colors cursor-pointer">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <Identity
                address={address}
                schemaId="0xf8b05c79f090979bf4a80270aba232dff11a10d9ca55c4f88de95317970f0de9"
              >
                <Avatar className="w-6 h-6" />
                <Name className="text-sm font-medium" />
              </Identity>
            </div>
            <WalletDropdownLink
              icon="wallet"
              href="https://wallet.coinbase.com"
              target="_blank"
              rel="noopener noreferrer"
            >
              Wallet
            </WalletDropdownLink>
            <WalletDropdownDisconnect />
          </WalletDropdown>
        </Wallet>
      )}
    </div>
  );
}

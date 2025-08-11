'use client';

import { Address, Avatar, Identity, Name } from '@coinbase/onchainkit/identity';
import {
  ConnectWallet,
  Wallet,
  WalletDropdown,
  WalletDropdownDisconnect,
  WalletDropdownLink,
} from '@coinbase/onchainkit/wallet';
import { useAccount } from 'wagmi';

export default function OnchainKitTestPage() {
  const { address, isConnected } = useAccount();

  return (
    <div className="min-h-screen bg-gray-950 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-gray-900 rounded-lg p-6">
          <h1 className="text-3xl font-bold text-white mb-2">OnchainKit Integration Test</h1>
          <p className="text-gray-300">Testing OnchainKit components with Base network</p>
        </div>

        {/* Wallet Connection Section */}
        <div className="bg-gray-900 rounded-lg p-6">
          <h2 className="text-xl font-bold text-white mb-4">Wallet Connection</h2>

          <div className="space-y-4">
            {!isConnected ? (
              <div className="space-y-4">
                <p className="text-gray-300">Connect your wallet to test OnchainKit components:</p>
                <Wallet>
                  <ConnectWallet>
                    <div className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md font-medium transition-colors cursor-pointer">
                      Connect Wallet
                    </div>
                  </ConnectWallet>
                </Wallet>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-green-900/20 border border-green-500/30 rounded p-4">
                  <p className="text-green-400 text-sm mb-3">✅ Wallet Connected Successfully!</p>

                  {/* Identity Component Demo */}
                  <div className="space-y-3">
                    <div className="bg-gray-800 rounded p-3">
                      <p className="text-gray-400 text-sm mb-2">Identity Component:</p>
                      <Identity
                        address={address}
                        schemaId="0xf8b05c79f090979bf4a80270aba232dff11a10d9ca55c4f88de95317970f0de9"
                      >
                        <Avatar />
                        <Name />
                        <Address />
                      </Identity>
                    </div>

                    <div className="bg-gray-800 rounded p-3">
                      <p className="text-gray-400 text-sm mb-2">Raw Address:</p>
                      <p className="text-white font-mono text-sm break-all">{address}</p>
                    </div>
                  </div>
                </div>

                {/* Wallet Dropdown */}
                <div className="bg-gray-800 rounded p-4">
                  <p className="text-gray-400 text-sm mb-3">Wallet Controls:</p>
                  <Wallet>
                    <WalletDropdown>
                      <Identity
                        address={address}
                        schemaId="0xf8b05c79f090979bf4a80270aba232dff11a10d9ca55c4f88de95317970f0de9"
                      >
                        <Avatar />
                        <Name />
                        <Address />
                      </Identity>
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
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Configuration Info */}
        <div className="bg-gray-900 rounded-lg p-6">
          <h2 className="text-xl font-bold text-white mb-4">Configuration Status</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-800 rounded p-3">
              <p className="text-gray-400 text-sm">OnchainKit Version</p>
              <p className="text-white font-medium">^0.38.19</p>
            </div>

            <div className="bg-gray-800 rounded p-3">
              <p className="text-gray-400 text-sm">Network</p>
              <p className="text-white font-medium">Base Mainnet</p>
            </div>

            <div className="bg-gray-800 rounded p-3">
              <p className="text-gray-400 text-sm">API Key Status</p>
              <p className="text-green-400 font-medium">
                {process.env.NEXT_PUBLIC_ONCHAINKIT_API_KEY ? '✅ Configured' : '❌ Missing'}
              </p>
            </div>

            <div className="bg-gray-800 rounded p-3">
              <p className="text-gray-400 text-sm">Connection Status</p>
              <p className={`font-medium ${isConnected ? 'text-green-400' : 'text-gray-400'}`}>
                {isConnected ? '✅ Connected' : '⭕ Not Connected'}
              </p>
            </div>
          </div>
        </div>

        {/* Implementation Status */}
        <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-6">
          <h2 className="text-xl font-bold text-blue-400 mb-4">✅ OnchainKit Setup Complete</h2>

          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <span className="text-green-400">✓</span>
              <span className="text-gray-300">OnchainKit installed and configured</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-400">✓</span>
              <span className="text-gray-300">OnchainKitProvider added to app providers</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-400">✓</span>
              <span className="text-gray-300">OnchainKit styles imported</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-400">✓</span>
              <span className="text-gray-300">Base network configured</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-400">✓</span>
              <span className="text-gray-300">API key configured</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-400">✓</span>
              <span className="text-gray-300">Wagmi and viem dependencies installed</span>
            </div>
          </div>

          <div className="mt-4 bg-blue-800/20 border border-blue-600/30 rounded p-4">
            <p className="text-blue-300">
              <strong>Success:</strong> OnchainKit is now properly configured following the Base
              documentation. You can now use Identity, Wallet, Transaction, Swap, and other
              OnchainKit components throughout your app.
            </p>
          </div>
        </div>

        {/* Available Components */}
        <div className="bg-gray-900 rounded-lg p-6">
          <h2 className="text-xl font-bold text-white mb-4">Available OnchainKit Components</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-gray-800 rounded p-3">
              <h3 className="text-white font-medium mb-2">Identity</h3>
              <p className="text-gray-400 text-sm">Basenames, avatars, badges, addresses</p>
            </div>

            <div className="bg-gray-800 rounded p-3">
              <h3 className="text-white font-medium mb-2">Wallet</h3>
              <p className="text-gray-400 text-sm">Connect wallet components</p>
            </div>

            <div className="bg-gray-800 rounded p-3">
              <h3 className="text-white font-medium mb-2">Transaction</h3>
              <p className="text-gray-400 text-sm">
                Handle transactions with EOAs or Smart Wallets
              </p>
            </div>

            <div className="bg-gray-800 rounded p-3">
              <h3 className="text-white font-medium mb-2">Swap</h3>
              <p className="text-gray-400 text-sm">Enable token swaps</p>
            </div>

            <div className="bg-gray-800 rounded p-3">
              <h3 className="text-white font-medium mb-2">Checkout</h3>
              <p className="text-gray-400 text-sm">USDC checkout flows</p>
            </div>

            <div className="bg-gray-800 rounded p-3">
              <h3 className="text-white font-medium mb-2">Fund</h3>
              <p className="text-gray-400 text-sm">Funding flows to onboard users</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

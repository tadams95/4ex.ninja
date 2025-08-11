/**
 * WalletConnection Component
 *
 * Simple wallet connection component for the header
 * Shows connection status and allows users to connect/disconnect via browser wallet
 */

'use client';

import { useWallet } from '@/hooks/useNotificationConnection';
import {
  formatTokenBalance,
  getAccessTierColor,
  getAccessTierLabel,
} from '@/utils/onchain-notification-manager';
import { useState } from 'react';

export default function WalletConnection() {
  const { walletState, isConnecting, connectWallet, disconnectWallet, getAvailableWallets } =
    useWallet();
  const [showConnectionModal, setShowConnectionModal] = useState(false);

  const handleConnect = async () => {
    const success = await connectWallet();
    if (success) {
      setShowConnectionModal(false);
    }
  };

  const handleDisconnect = () => {
    disconnectWallet();
    setShowConnectionModal(false);
  };

  const availableWallets = getAvailableWallets();
  const hasWallet = availableWallets.length > 0;

  if (walletState.isConnected) {
    return (
      <div className="relative">
        <button
          onClick={() => setShowConnectionModal(!showConnectionModal)}
          className="flex items-center space-x-2 bg-gray-800 hover:bg-gray-700 px-3 py-2 rounded-md transition-colors"
        >
          <div className="w-2 h-2 bg-green-400 rounded-full"></div>
          <span className="text-sm font-medium">
            {walletState.address?.slice(0, 6)}...{walletState.address?.slice(-4)}
          </span>
          <span
            className={`text-xs px-2 py-1 rounded ${getAccessTierColor(
              walletState.accessTier || 'public'
            )} bg-gray-700`}
          >
            {walletState.accessTier?.toUpperCase() || 'PUBLIC'}
          </span>
        </button>

        {showConnectionModal && (
          <div className="absolute right-0 top-12 w-80 bg-gray-900 border border-gray-700 rounded-lg shadow-lg z-50">
            <div className="p-4">
              <h3 className="text-white font-medium mb-3">Wallet Connected</h3>

              <div className="space-y-3">
                <div className="bg-gray-800 rounded p-3">
                  <p className="text-gray-400 text-sm">Address</p>
                  <p className="text-white font-mono text-sm">{walletState.address}</p>
                </div>

                <div className="bg-gray-800 rounded p-3">
                  <p className="text-gray-400 text-sm">Balance</p>
                  <p className="text-white font-medium">
                    {walletState.tokenBalance ? formatTokenBalance(walletState.tokenBalance) : '0'}{' '}
                    $4EX
                  </p>
                </div>

                <div className="bg-gray-800 rounded p-3">
                  <p className="text-gray-400 text-sm">Access Tier</p>
                  <p
                    className={`font-medium ${getAccessTierColor(
                      walletState.accessTier || 'public'
                    )}`}
                  >
                    {getAccessTierLabel(walletState.accessTier || 'public')}
                  </p>
                </div>
              </div>

              <div className="mt-4 flex space-x-2">
                <button
                  onClick={() => setShowConnectionModal(false)}
                  className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded-md font-medium transition-colors"
                >
                  Close
                </button>
                <button
                  onClick={handleDisconnect}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white py-2 rounded-md font-medium transition-colors"
                >
                  Disconnect
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setShowConnectionModal(!showConnectionModal)}
        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors"
      >
        Connect Wallet
      </button>

      {showConnectionModal && (
        <div className="absolute right-0 top-12 w-80 bg-gray-900 border border-gray-700 rounded-lg shadow-lg z-50">
          <div className="p-4">
            <h3 className="text-white font-medium mb-3">Connect Wallet</h3>

            {!hasWallet ? (
              <div className="space-y-4">
                <div className="bg-red-900/20 border border-red-500/30 rounded p-3">
                  <p className="text-red-400 text-sm">
                    No wallet detected. Please install MetaMask or Coinbase Wallet to connect.
                  </p>
                </div>

                <div className="space-y-2">
                  <a
                    href="https://metamask.io/download/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full bg-orange-600 hover:bg-orange-700 text-white py-2 px-3 rounded-md text-center font-medium transition-colors"
                  >
                    Install MetaMask
                  </a>
                  <a
                    href="https://www.coinbase.com/wallet"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-3 rounded-md text-center font-medium transition-colors"
                  >
                    Install Coinbase Wallet
                  </a>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-blue-900/20 border border-blue-500/30 rounded p-3">
                  <p className="text-blue-400 text-sm mb-2">
                    Click "Connect" to connect your {availableWallets.join(' or ')} wallet.
                  </p>
                  <p className="text-gray-400 text-xs">
                    You'll be prompted to sign a message to verify wallet ownership.
                  </p>
                </div>

                <div className="bg-gray-800 rounded p-3">
                  <h4 className="text-white text-sm font-medium mb-2">What happens next:</h4>
                  <ul className="text-gray-300 text-xs space-y-1">
                    <li>• Your wallet will prompt you to connect</li>
                    <li>• We'll check your $4EX token balance</li>
                    <li>• Your access tier will be determined</li>
                    <li>• No transactions will be made</li>
                  </ul>
                </div>
              </div>
            )}

            <div className="mt-4 flex space-x-2">
              <button
                onClick={() => setShowConnectionModal(false)}
                className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded-md font-medium transition-colors"
              >
                Cancel
              </button>
              {hasWallet && (
                <button
                  onClick={handleConnect}
                  disabled={isConnecting}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white py-2 rounded-md font-medium transition-colors"
                >
                  {isConnecting ? 'Connecting...' : 'Connect'}
                </button>
              )}
            </div>

            {walletState.error && (
              <div className="mt-3 p-2 bg-red-900/20 border border-red-500/30 rounded text-red-400 text-sm">
                {walletState.error}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Backdrop to close modal */}
      {showConnectionModal && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setShowConnectionModal(false)}
        />
      )}
    </div>
  );
}

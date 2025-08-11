/**
 * WalletConnection Component
 *
 * Simple wallet connection component for the header
 * Shows connection status and allows users to connect/disconnect
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
  const { walletState, isConnecting, connectWallet, disconnectWallet } = useWallet();
  const [showConnectionModal, setShowConnectionModal] = useState(false);
  const [walletInput, setWalletInput] = useState('');

  const handleConnect = async () => {
    if (!walletInput.trim()) return;

    const success = await connectWallet(walletInput.trim());
    if (success) {
      setWalletInput('');
      setShowConnectionModal(false);
    }
  };

  const handleDisconnect = () => {
    disconnectWallet();
    setShowConnectionModal(false);
  };

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

            <div className="space-y-3">
              <div>
                <label className="block text-gray-400 text-sm mb-2">Wallet Address</label>
                <input
                  type="text"
                  value={walletInput}
                  onChange={e => setWalletInput(e.target.value)}
                  placeholder="Enter wallet address (0x...)"
                  className="w-full bg-gray-800 border border-gray-600 rounded-md px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Test Addresses */}
              <div className="bg-gray-800 rounded p-3">
                <p className="text-gray-400 text-xs mb-2">Quick test addresses:</p>
                <div className="space-y-1">
                  <button
                    onClick={() => setWalletInput('0x1234567890abcdef1234567890abcdef12345670')}
                    className="block w-full text-left text-purple-400 hover:text-purple-300 text-xs p-1 rounded hover:bg-gray-700"
                  >
                    Whale: 0x...70 (100,000+ $4EX)
                  </button>
                  <button
                    onClick={() => setWalletInput('0x1234567890abcdef1234567890abcdef12345671')}
                    className="block w-full text-left text-yellow-400 hover:text-yellow-300 text-xs p-1 rounded hover:bg-gray-700"
                  >
                    Premium: 0x...71 (10,000+ $4EX)
                  </button>
                  <button
                    onClick={() => setWalletInput('0x1234567890abcdef1234567890abcdef12345672')}
                    className="block w-full text-left text-blue-400 hover:text-blue-300 text-xs p-1 rounded hover:bg-gray-700"
                  >
                    Holder: 0x...72 (1,000+ $4EX)
                  </button>
                  <button
                    onClick={() => setWalletInput('0x1234567890abcdef1234567890abcdef12345673')}
                    className="block w-full text-left text-gray-400 hover:text-gray-300 text-xs p-1 rounded hover:bg-gray-700"
                  >
                    Free: 0x...73 (0 $4EX)
                  </button>
                </div>
              </div>
            </div>

            <div className="mt-4 flex space-x-2">
              <button
                onClick={() => setShowConnectionModal(false)}
                className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded-md font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConnect}
                disabled={isConnecting || !walletInput.trim()}
                className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white py-2 rounded-md font-medium transition-colors"
              >
                {isConnecting ? 'Connecting...' : 'Connect'}
              </button>
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

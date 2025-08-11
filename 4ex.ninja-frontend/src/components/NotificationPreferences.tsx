/**
 * Notification Preferences Component
 * Day 3-4: UI for managing onchain-aware notification settings
 */

'use client';

import {
  useNotificationConnection,
  useNotificationPreferences,
  useWalletNotifications,
} from '@/hooks/useNotificationConnection';
import { useState } from 'react';

interface NotificationPreferencesProps {
  className?: string;
}

export default function NotificationPreferences({ className = '' }: NotificationPreferencesProps) {
  const {
    preferences,
    toggleSounds,
    toggleBrowserPush,
    updateMinimumConfidence,
    updateSignalTypes,
  } = useNotificationPreferences();
  const { walletAddress, isWalletConnected, connectWallet, isConnecting, accessTier } =
    useWalletNotifications();
  const { connected, authType, subscribeToTokenGatedSignals } = useNotificationConnection();

  const [testWalletAddress, setTestWalletAddress] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);

  const handleWalletConnect = async () => {
    if (!testWalletAddress) return;
    try {
      await connectWallet(testWalletAddress);
    } catch (error) {
      console.error('Failed to connect wallet:', error);
    }
  };

  const handleSignalTypeChange = (signalType: string, checked: boolean) => {
    const currentTypes = preferences.signalTypes || [];
    const newTypes = checked
      ? [...currentTypes, signalType]
      : currentTypes.filter(type => type !== signalType);
    updateSignalTypes(newTypes);
  };

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          🔔 Notification Preferences
        </h3>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
        >
          {isExpanded ? 'Collapse' : 'Expand'}
        </button>
      </div>

      {/* Connection Status */}
      <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Connection Status
          </span>
          <span
            className={`px-2 py-1 rounded-full text-xs font-medium ${
              connected
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
            }`}
          >
            {connected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
        </div>

        {connected && (
          <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
            <div>
              Auth Type: <span className="font-medium">{authType}</span>
            </div>
            <div>
              Access Tier: <span className="font-medium capitalize">{accessTier}</span>
            </div>
            {walletAddress && (
              <div>
                Wallet:{' '}
                <span className="font-mono text-xs">
                  {walletAddress.slice(0, 6)}...{walletAddress.slice(-4)}
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Wallet Connection */}
      {!isWalletConnected && isExpanded && (
        <div className="mb-6 p-4 border-2 border-dashed border-blue-300 dark:border-blue-600 rounded-lg">
          <h4 className="text-md font-medium mb-3 text-gray-900 dark:text-white">
            🪙 Connect Wallet for Token-Gated Notifications
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Connect your wallet to access premium signal channels based on your $4EX token holdings.
          </p>

          <div className="flex gap-2">
            <input
              type="text"
              placeholder="0x1234567890abcdef... (test wallet)"
              value={testWalletAddress}
              onChange={e => setTestWalletAddress(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm 
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              onClick={handleWalletConnect}
              disabled={!testWalletAddress || isConnecting}
              className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium
                         hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
                         transition-colors"
            >
              {isConnecting ? 'Connecting...' : 'Connect'}
            </button>
          </div>

          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            For testing: Use addresses ending in 0 (whale), 1 (holder), 2 (premium), or other (free)
          </p>
        </div>
      )}

      {/* Access Tier Benefits */}
      {isWalletConnected && isExpanded && (
        <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg">
          <h4 className="text-md font-medium mb-3 text-gray-900 dark:text-white">
            🎯 Your Access Level:{' '}
            <span className="capitalize text-blue-600 dark:text-blue-400">{accessTier}</span>
          </h4>

          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-green-600 dark:text-green-400">✅</span>
              <span className="text-gray-600 dark:text-gray-300">Public Signals</span>
            </div>
            {(accessTier === 'premium' || accessTier === 'holder' || accessTier === 'whale') && (
              <div className="flex items-center gap-2">
                <span className="text-green-600 dark:text-green-400">✅</span>
                <span className="text-gray-600 dark:text-gray-300">Premium Signals</span>
              </div>
            )}
            {(accessTier === 'holder' || accessTier === 'whale') && (
              <div className="flex items-center gap-2">
                <span className="text-green-600 dark:text-green-400">✅</span>
                <span className="text-gray-600 dark:text-gray-300">Holder Exclusive</span>
              </div>
            )}
            {accessTier === 'whale' && (
              <div className="flex items-center gap-2">
                <span className="text-green-600 dark:text-green-400">✅</span>
                <span className="text-gray-600 dark:text-gray-300">Whale Alpha</span>
              </div>
            )}
          </div>

          {(accessTier === 'premium' || accessTier === 'holder' || accessTier === 'whale') && (
            <button
              onClick={() => subscribeToTokenGatedSignals('premium')}
              className="mt-3 px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition-colors"
            >
              Subscribe to Premium Signals
            </button>
          )}
        </div>
      )}

      {/* Basic Preferences */}
      <div className="space-y-4">
        {/* Sound Settings */}
        <div className="flex items-center justify-between">
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              🔊 Sound Notifications
            </label>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Play sound when new signals arrive
            </p>
          </div>
          <button
            onClick={toggleSounds}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              preferences.sounds ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-600'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                preferences.sounds ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        {/* Browser Push Settings */}
        <div className="flex items-center justify-between">
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              📱 Browser Push Notifications
            </label>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Receive notifications even when tab is closed
            </p>
          </div>
          <button
            onClick={toggleBrowserPush}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              preferences.browserPush ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-600'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                preferences.browserPush ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        {isExpanded && (
          <>
            {/* Minimum Confidence */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                📊 Minimum Signal Confidence: {Math.round(preferences.minimumConfidence * 100)}%
              </label>
              <input
                type="range"
                min="0.5"
                max="0.95"
                step="0.05"
                value={preferences.minimumConfidence}
                onChange={e => updateMinimumConfidence(parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
              />
              <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
                <span>50%</span>
                <span>95%</span>
              </div>
            </div>

            {/* Signal Types */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                📈 Signal Types
              </label>
              <div className="space-y-2">
                {['BUY', 'SELL'].map(signalType => (
                  <label key={signalType} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={preferences.signalTypes?.includes(signalType) || false}
                      onChange={e => handleSignalTypeChange(signalType, e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50 dark:border-gray-600 dark:bg-gray-700"
                    />
                    <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                      {signalType} Signals
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Migration Notice */}
      {isExpanded && (
        <div className="mt-6 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-sm text-blue-700 dark:text-blue-300">
            <span className="font-medium">🚀 Future Enhancement:</span> Your preferences will be
            stored onchain when the $4EX token launches, providing decentralized preference
            management across all devices.
          </p>
        </div>
      )}
    </div>
  );
}

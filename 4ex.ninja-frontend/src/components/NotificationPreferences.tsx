/**
 * NotificationPreferences Component
 * 
 * UI for managing wallet connections, notification settings,
 * and token tier visualization with real onchain integration
 */

'use client';

import React, { useState } from 'react';
import { 
  useWalletNotifications, 
  useNotificationPreferences, 
  useConnectionStatus 
} from '@/hooks/useNotificationConnection';
import { 
  formatTokenBalance, 
  getAccessTierLabel, 
  getAccessTierColor,
  type AccessTier 
} from '@/utils/onchain-notification-manager';

export default function NotificationPreferences() {
  const { walletState, connectWallet, disconnectWallet, getAvailableChannels } = useWalletNotifications();
  const { preferences, updatePreferences, hasPermission, requestNotificationPermission, sendTestNotification } = useNotificationPreferences();
  const connectionStatus = useConnectionStatus();
  
  const [walletInput, setWalletInput] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);

  const handleConnectWallet = async () => {
    if (!walletInput.trim()) return;
    
    setIsConnecting(true);
    try {
      const success = await connectWallet(walletInput.trim());
      if (success) {
        setWalletInput('');
      }
    } catch (error) {
      console.error('Wallet connection failed:', error);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleBrowserPushToggle = async () => {
    if (!preferences.browserPush && hasPermission !== 'granted') {
      const permission = await requestNotificationPermission();
      if (permission === 'granted') {
        updatePreferences({ browserPush: true });
      }
    } else {
      updatePreferences({ browserPush: !preferences.browserPush });
    }
  };

  const availableChannels = getAvailableChannels(walletState.accessTier);

  return (
    <div className="bg-gray-900 rounded-lg p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Notification Preferences</h2>
        <div className="flex items-center space-x-2 text-sm">
          <span className={connectionStatus.color}>{connectionStatus.icon}</span>
          <span className={connectionStatus.color}>{connectionStatus.message}</span>
        </div>
      </div>

      {/* Wallet Connection Section */}
      <div className="border border-gray-700 rounded-lg p-4 space-y-4">
        <h3 className="text-lg font-semibold text-white">Wallet Connection</h3>
        
        {!walletState.isConnected ? (
          <div className="space-y-3">
            <p className="text-gray-300 text-sm">
              Connect your wallet to access token-gated notifications and premium features.
            </p>
            
            <div className="flex space-x-2">
              <input
                type="text"
                value={walletInput}
                onChange={(e) => setWalletInput(e.target.value)}
                placeholder="Enter wallet address (0x...)"
                className="flex-1 bg-gray-800 border border-gray-600 rounded-md px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleConnectWallet}
                disabled={isConnecting || !walletInput.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded-md font-medium transition-colors"
              >
                {isConnecting ? 'Connecting...' : 'Connect'}
              </button>
            </div>

            {/* Test Addresses */}
            <div className="bg-gray-800 rounded-md p-3">
              <p className="text-gray-300 text-xs mb-2">Test addresses for different tiers:</p>
              <div className="space-y-1 text-xs">
                <button
                  onClick={() => setWalletInput('0x1234567890abcdef1234567890abcdef12345670')}
                  className="block text-purple-400 hover:text-purple-300 cursor-pointer"
                >
                  Whale: 0x...70 (100,000+ $4EX)
                </button>
                <button
                  onClick={() => setWalletInput('0x1234567890abcdef1234567890abcdef12345671')}
                  className="block text-yellow-400 hover:text-yellow-300 cursor-pointer"
                >
                  Premium: 0x...71 (10,000+ $4EX)
                </button>
                <button
                  onClick={() => setWalletInput('0x1234567890abcdef1234567890abcdef12345672')}
                  className="block text-blue-400 hover:text-blue-300 cursor-pointer"
                >
                  Holder: 0x...72 (1,000+ $4EX)
                </button>
                <button
                  onClick={() => setWalletInput('0x1234567890abcdef1234567890abcdef12345673')}
                  className="block text-gray-400 hover:text-gray-300 cursor-pointer"
                >
                  Free: 0x...73 (0 $4EX)
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between bg-gray-800 rounded-md p-3">
              <div>
                <p className="text-white font-medium">
                  {walletState.address?.slice(0, 6)}...{walletState.address?.slice(-4)}
                </p>
                <p className="text-gray-300 text-sm">
                  Balance: {walletState.tokenBalance ? formatTokenBalance(walletState.tokenBalance) : '0'} $4EX
                </p>
              </div>
              <div className="text-right">
                <p className={`font-medium ${getAccessTierColor(walletState.accessTier || 'public')}`}>
                  {getAccessTierLabel(walletState.accessTier || 'public')}
                </p>
                <button
                  onClick={disconnectWallet}
                  className="text-red-400 hover:text-red-300 text-sm"
                >
                  Disconnect
                </button>
              </div>
            </div>

            {/* Access Tier Benefits */}
            <div className="bg-gray-800 rounded-md p-3">
              <h4 className="text-white font-medium mb-2">Your Access Benefits:</h4>
              <div className="space-y-1 text-sm">
                {availableChannels.length > 0 ? (
                  availableChannels.map((channel) => (
                    <div key={channel} className="flex items-center space-x-2">
                      <span className="text-green-400">✓</span>
                      <span className="text-gray-300 capitalize">{channel.replace('_', ' ')}</span>
                    </div>
                  ))
                ) : (
                  <div className="flex items-center space-x-2">
                    <span className="text-blue-400">ℹ️</span>
                    <span className="text-gray-300">Public signals only</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Notification Settings */}
      <div className="border border-gray-700 rounded-lg p-4 space-y-4">
        <h3 className="text-lg font-semibold text-white">Notification Settings</h3>
        
        {/* Sound Notifications */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-white font-medium">Sound Notifications</p>
            <p className="text-gray-400 text-sm">Play sound when new signals arrive</p>
          </div>
          <button
            onClick={() => updatePreferences({ sounds: !preferences.sounds })}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              preferences.sounds ? 'bg-blue-600' : 'bg-gray-600'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 rounded-full bg-white transition-transform ${
                preferences.sounds ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        {/* Browser Push Notifications */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-white font-medium">Browser Push Notifications</p>
            <p className="text-gray-400 text-sm">Get notifications even when tab is closed</p>
          </div>
          <div className="flex items-center space-x-2">
            {hasPermission === 'denied' && (
              <span className="text-red-400 text-xs">Blocked</span>
            )}
            <button
              onClick={handleBrowserPushToggle}
              disabled={hasPermission === 'denied'}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                preferences.browserPush ? 'bg-blue-600' : 'bg-gray-600'
              } ${hasPermission === 'denied' ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <span
                className={`inline-block h-4 w-4 rounded-full bg-white transition-transform ${
                  preferences.browserPush ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>

        {/* Test Notification */}
        {preferences.browserPush && hasPermission === 'granted' && (
          <button
            onClick={sendTestNotification}
            className="w-full bg-gray-700 hover:bg-gray-600 text-white py-2 rounded-md font-medium transition-colors"
          >
            Send Test Notification
          </button>
        )}

        {/* Signal Types */}
        <div>
          <p className="text-white font-medium mb-2">Signal Types</p>
          <div className="space-y-2">
            {['BUY', 'SELL', 'ALERT'].map((type) => (
              <label key={type} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferences.signalTypes.includes(type)}
                  onChange={(e) => {
                    const newTypes = e.target.checked
                      ? [...preferences.signalTypes, type]
                      : preferences.signalTypes.filter(t => t !== type);
                    updatePreferences({ signalTypes: newTypes });
                  }}
                  className="rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-gray-300">{type} signals</span>
              </label>
            ))}
          </div>
        </div>

        {/* Minimum Confidence */}
        <div>
          <p className="text-white font-medium mb-2">
            Minimum Confidence: {preferences.minimumConfidence}%
          </p>
          <input
            type="range"
            min="50"
            max="95"
            step="5"
            value={preferences.minimumConfidence}
            onChange={(e) => updatePreferences({ minimumConfidence: parseInt(e.target.value) })}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>50%</span>
            <span>95%</span>
          </div>
        </div>
      </div>

      {/* Onchain Migration Info */}
      <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
        <h3 className="text-blue-400 font-medium mb-2">🚀 Onchain Migration Ready</h3>
        <p className="text-gray-300 text-sm mb-3">
          When the $4EX token launches, your preferences will automatically migrate to onchain storage 
          for enhanced security and cross-device synchronization.
        </p>
        <div className="space-y-1 text-xs">
          <div className="flex items-center space-x-2">
            <span className="text-green-400">✓</span>
            <span className="text-gray-300">Wallet connection infrastructure ready</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-green-400">✓</span>
            <span className="text-gray-300">Token balance monitoring implemented</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-green-400">✓</span>
            <span className="text-gray-300">Dynamic access tier updates configured</span>
          </div>
        </div>
      </div>
    </div>
  );
}

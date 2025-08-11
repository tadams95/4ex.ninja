/**
 * WebSocket Notification Test Page
 * Day 3-4: Test implementation of onchain-aware WebSocket client
 */

'use client';

import NotificationPreferences from '@/components/NotificationPreferences';
import RealTimeNotifications, { NotificationWidget } from '@/components/RealTimeNotifications';
import { useNotificationConnection } from '@/hooks/useNotificationConnection';
import { useState } from 'react';

export default function WebSocketTestPage() {
  const { connected, authType, accessTier, error, clearError } = useNotificationConnection();
  const [testSignalSent, setTestSignalSent] = useState(false);

  const sendTestSignal = () => {
    // Simulate receiving a test signal (in real implementation, this comes from backend)
    const testNotification = {
      type: 'signal' as const,
      data: {
        signal_id: `test_${Date.now()}`,
        pair: 'EUR_USD',
        signal_type: 'BUY' as const,
        entry_price: 1.095,
        confidence_score: 0.85,
        timestamp: new Date().toISOString(),
        channel: accessTier === 'whale' ? 'whale' : accessTier === 'holder' ? 'premium' : 'public',
      },
      timestamp: new Date().toISOString(),
    };

    // For testing purposes, we can manually trigger the notification handler
    // In production, this comes through the WebSocket connection
    console.log('Test signal would be:', testNotification);
    setTestSignalSent(true);
    setTimeout(() => setTestSignalSent(false), 3000);
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 p-4">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            🚀 Day 3-4: Onchain-Aware WebSocket Client Test
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Testing multi-auth WebSocket notifications with token-gated channel access
          </p>

          {/* Connection Status Widget */}
          <div className="mt-4 flex items-center justify-between">
            <NotificationWidget />
            {error && (
              <div className="flex items-center gap-2">
                <span className="text-red-600 dark:text-red-400 text-sm">Error: {error}</span>
                <button
                  onClick={clearError}
                  className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 text-sm underline"
                >
                  Clear
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Implementation Status */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            ✅ Implementation Status
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-green-600 dark:text-green-400">✅</span>
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  OnchainNotificationManager class
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-green-600 dark:text-green-400">✅</span>
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Multi-auth support (wallet/session/anonymous)
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-green-600 dark:text-green-400">✅</span>
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Token-gated notification channels
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-green-600 dark:text-green-400">✅</span>
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Local preference storage
                </span>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-green-600 dark:text-green-400">✅</span>
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  React hooks for easy integration
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-green-600 dark:text-green-400">✅</span>
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Browser push notification support
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-green-600 dark:text-green-400">✅</span>
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Real-time token balance monitoring (simulated)
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-green-600 dark:text-green-400">✅</span>
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Onchain migration readiness
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Test Controls */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            🧪 Test Controls
          </h2>

          <div className="flex flex-wrap gap-3">
            <button
              onClick={sendTestSignal}
              disabled={!connected}
              className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium
                         hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
                         transition-colors"
            >
              {testSignalSent ? 'Signal Sent! 📡' : 'Send Test Signal'}
            </button>

            <div className="text-sm text-gray-600 dark:text-gray-400 flex items-center">
              Status:
              <span
                className={`ml-1 font-medium ${
                  connected
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400'
                }`}
              >
                {connected ? `Connected (${authType})` : 'Disconnected'}
              </span>
            </div>
          </div>

          <p className="text-xs text-gray-500 dark:text-gray-400 mt-3">
            Note: In production, signals come from the backend WebSocket server. This test button
            simulates the notification handling.
          </p>
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Notification Preferences */}
          <NotificationPreferences />

          {/* Real-time Notifications */}
          <RealTimeNotifications />
        </div>

        {/* Future Features */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            🔮 Future Onchain Features (Ready for Implementation)
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-blue-600 dark:text-blue-400">🔄</span>
                <span className="text-gray-700 dark:text-gray-300">
                  Real-time $4EX token balance monitoring
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-blue-600 dark:text-blue-400">🔄</span>
                <span className="text-gray-700 dark:text-gray-300">
                  Onchain preference storage via smart contract
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-blue-600 dark:text-blue-400">🔄</span>
                <span className="text-gray-700 dark:text-gray-300">
                  Dynamic access tier updates based on holdings
                </span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-blue-600 dark:text-blue-400">🔄</span>
                <span className="text-gray-700 dark:text-gray-300">
                  Wallet signature verification for auth
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-blue-600 dark:text-blue-400">🔄</span>
                <span className="text-gray-700 dark:text-gray-300">
                  Cross-device sync via wallet identity
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-blue-600 dark:text-blue-400">🔄</span>
                <span className="text-gray-700 dark:text-gray-300">
                  NFT-based exclusive channel access
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

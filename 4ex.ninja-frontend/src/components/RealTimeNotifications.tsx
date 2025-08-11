/**
 * RealTimeNotifications Component
 * 
 * Displays live signals with wallet-aware features,
 * filtering, and access tier visualization
 */

'use client';

import React, { useState, useEffect } from 'react';
import { 
  useNotificationConnection, 
  useWalletNotifications, 
  useNotificationPreferences,
  useAudioNotifications,
  useConnectionStatus 
} from '@/hooks/useNotificationConnection';
import { getAccessTierColor, type AccessTier } from '@/utils/onchain-notification-manager';

interface Signal {
  id: string;
  type: 'BUY' | 'SELL' | 'ALERT';
  pair: string;
  confidence: number;
  price: number;
  timestamp: number;
  accessTier: AccessTier;
  channel?: string;
}

interface RealTimeNotificationsProps {
  variant?: 'full' | 'compact';
  maxItems?: number;
}

export default function RealTimeNotifications({ 
  variant = 'full', 
  maxItems = 50 
}: RealTimeNotificationsProps) {
  const { notifications, unreadCount, markAsRead, clearNotifications, connectionState } = useNotificationConnection();
  const { walletState } = useWalletNotifications();
  const { preferences } = useNotificationPreferences();
  const { playNotificationSound } = useAudioNotifications();
  const connectionStatus = useConnectionStatus();
  
  const [filter, setFilter] = useState<'ALL' | 'BUY' | 'SELL' | 'ALERT'>('ALL');
  const [showOnlyAccessible, setShowOnlyAccessible] = useState(false);

  // Play sound for new notifications
  useEffect(() => {
    if (notifications.length > 0 && preferences.sounds) {
      const latestNotification = notifications[0];
      playNotificationSound(latestNotification.type === 'ALERT' ? 'alert' : 'signal');
    }
  }, [notifications.length, preferences.sounds, playNotificationSound]);

  // Show browser notification for new signals
  useEffect(() => {
    if (notifications.length > 0 && preferences.browserPush && 'Notification' in window && Notification.permission === 'granted') {
      const latest = notifications[0];
      if (latest.type === 'signal' || latest.type === 'notification') {
        new Notification(`4ex.ninja - ${latest.data?.type || 'Signal'}`, {
          body: `${latest.data?.pair || 'Unknown'} - Confidence: ${latest.data?.confidence || 0}%`,
          icon: '/favicon.ico',
          tag: `signal-${latest.data?.id}`,
        });
      }
    }
  }, [notifications.length, preferences.browserPush]);

  // Filter notifications based on user preferences and access
  const filteredNotifications = notifications
    .filter(notif => {
      // Filter by type
      if (filter !== 'ALL' && notif.data?.type !== filter) return false;
      
      // Filter by confidence
      if (notif.data?.confidence < preferences.minimumConfidence) return false;
      
      // Filter by signal types
      if (!preferences.signalTypes.includes(notif.data?.type)) return false;
      
      // Filter by access if enabled
      if (showOnlyAccessible) {
        const userTier = walletState.accessTier || 'public';
        const notifTier = (notif.data?.accessTier as AccessTier) || 'public';
        
        // Check if user has access to this notification tier
        const tierHierarchy: Record<AccessTier, number> = { public: 0, holders: 1, premium: 2, whale: 3 };
        if (tierHierarchy[userTier] < tierHierarchy[notifTier]) return false;
      }
      
      return true;
    })
    .slice(0, maxItems);

  const handleMarkAsRead = () => {
    markAsRead();
  };

  if (variant === 'compact') {
    return (
      <div className="bg-gray-900 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-white font-medium">Live Signals</h3>
          <div className="flex items-center space-x-2">
            {unreadCount > 0 && (
              <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                {unreadCount}
              </span>
            )}
            <div className={`w-2 h-2 rounded-full ${connectionState === 'connected' ? 'bg-green-400' : 'bg-gray-400'}`} />
          </div>
        </div>
        
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {filteredNotifications.slice(0, 5).map((notif, index) => (
            <div key={`${notif.data?.id}-${index}`} className="bg-gray-800 rounded p-2 text-sm">
              <div className="flex items-center justify-between">
                <span className={`font-medium ${notif.data?.type === 'BUY' ? 'text-green-400' : notif.data?.type === 'SELL' ? 'text-red-400' : 'text-yellow-400'}`}>
                  {notif.data?.type} {notif.data?.pair}
                </span>
                <span className="text-gray-400 text-xs">
                  {notif.data?.confidence}%
                </span>
              </div>
            </div>
          ))}
          
          {filteredNotifications.length === 0 && (
            <p className="text-gray-400 text-center py-4">No signals available</p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-white">Real-Time Notifications</h2>
          <div className="flex items-center space-x-2 mt-1">
            <span className={connectionStatus.color}>{connectionStatus.icon}</span>
            <span className={`text-sm ${connectionStatus.color}`}>{connectionStatus.message}</span>
            {walletState.isConnected && (
              <span className={`text-xs px-2 py-1 rounded ${getAccessTierColor(walletState.accessTier || 'public')} bg-gray-800`}>
                {walletState.accessTier?.toUpperCase() || 'PUBLIC'}
              </span>
            )}
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAsRead}
              className="text-blue-400 hover:text-blue-300 text-sm"
            >
              Mark Read ({unreadCount})
            </button>
          )}
          <button
            onClick={clearNotifications}
            className="text-red-400 hover:text-red-300 text-sm"
          >
            Clear All
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="flex bg-gray-800 rounded-md p-1">
          {['ALL', 'BUY', 'SELL', 'ALERT'].map((type) => (
            <button
              key={type}
              onClick={() => setFilter(type as any)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                filter === type 
                  ? 'bg-blue-600 text-white' 
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
        
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showOnlyAccessible}
            onChange={(e) => setShowOnlyAccessible(e.target.checked)}
            className="rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-gray-300 text-sm">Only my access tier</span>
        </label>
      </div>

      {/* Notifications List */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {filteredNotifications.map((notif, index) => {
          const isAccessible = () => {
            const userTier = walletState.accessTier || 'public';
            const notifTier = (notif.data?.accessTier as AccessTier) || 'public';
            const tierHierarchy: Record<AccessTier, number> = { public: 0, holders: 1, premium: 2, whale: 3 };
            return tierHierarchy[userTier] >= tierHierarchy[notifTier];
          };

          return (
            <div 
              key={`${notif.data?.id}-${index}`}
              className={`bg-gray-800 rounded-lg p-4 border-l-4 ${
                notif.data?.type === 'BUY' 
                  ? 'border-green-400' 
                  : notif.data?.type === 'SELL' 
                    ? 'border-red-400' 
                    : 'border-yellow-400'
              } ${!isAccessible() ? 'opacity-50' : ''}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <span className={`font-bold text-lg ${
                      notif.data?.type === 'BUY' 
                        ? 'text-green-400' 
                        : notif.data?.type === 'SELL' 
                          ? 'text-red-400' 
                          : 'text-yellow-400'
                    }`}>
                      {notif.data?.type}
                    </span>
                    <span className="text-white font-medium text-lg">
                      {notif.data?.pair || 'Unknown Pair'}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded ${getAccessTierColor(notif.data?.accessTier || 'public')} bg-gray-700`}>
                      {(notif.data?.accessTier || 'public').toUpperCase()}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-400">Confidence:</span>
                      <span className={`ml-2 font-medium ${
                        (notif.data?.confidence || 0) >= 90 
                          ? 'text-green-400' 
                          : (notif.data?.confidence || 0) >= 80 
                            ? 'text-yellow-400' 
                            : 'text-gray-300'
                      }`}>
                        {notif.data?.confidence || 0}%
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">Price:</span>
                      <span className="text-white ml-2 font-medium">
                        {notif.data?.price || 'N/A'}
                      </span>
                    </div>
                  </div>

                  {notif.data?.message && (
                    <p className="text-gray-300 mt-2 text-sm">
                      {notif.data.message}
                    </p>
                  )}
                </div>
                
                <div className="text-right text-xs text-gray-400">
                  {new Date(notif.timestamp || Date.now()).toLocaleTimeString()}
                </div>
              </div>

              {!isAccessible() && (
                <div className="mt-3 bg-gray-700 rounded p-2">
                  <p className="text-yellow-400 text-xs">
                    🔒 Upgrade your access tier to view this signal
                  </p>
                </div>
              )}
            </div>
          );
        })}

        {filteredNotifications.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 text-lg mb-2">No signals available</div>
            <p className="text-gray-500 text-sm">
              {connectionState === 'connected' 
                ? 'Waiting for new signals...' 
                : 'Connect to start receiving signals'}
            </p>
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="mt-4 pt-4 border-t border-gray-700">
        <div className="flex justify-between items-center text-xs text-gray-400">
          <span>Total: {filteredNotifications.length} signals</span>
          <span>
            Access tier: {walletState.accessTier ? (
              <span className={getAccessTierColor(walletState.accessTier)}>
                {walletState.accessTier.toUpperCase()}
              </span>
            ) : (
              'PUBLIC'
            )}
          </span>
        </div>
      </div>
    </div>
  );
}

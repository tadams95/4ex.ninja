/**
 * Real-time Signal Notifications Component
 * Day 3-4: Display live signals from WebSocket with wallet-aware features
 */

'use client';

import { useNotificationConnection } from '@/hooks/useNotificationConnection';
import React, { useEffect, useState } from 'react';

interface RealTimeNotificationsProps {
  className?: string;
  maxDisplayCount?: number;
}

export default function RealTimeNotifications({
  className = '',
  maxDisplayCount = 10,
}: RealTimeNotificationsProps) {
  const { connected, authType, accessTier, notifications, unreadCount, markAsRead, markAllAsRead } =
    useNotificationConnection();

  const [isExpanded, setIsExpanded] = useState(false);
  const [filter, setFilter] = useState<'all' | 'BUY' | 'SELL'>('all');

  // Auto-expand when new notifications arrive
  useEffect(() => {
    if (unreadCount > 0 && !isExpanded) {
      setIsExpanded(true);
    }
  }, [unreadCount, isExpanded]);

  const filteredNotifications = notifications
    .filter(notification => filter === 'all' || notification.data.signal_type === filter)
    .slice(0, maxDisplayCount);

  const formatConfidence = (confidence: number): string => {
    return `${Math.round(confidence * 100)}%`;
  };

  const formatPrice = (price: number): string => {
    return price.toFixed(5);
  };

  const formatTime = (timestamp: string): string => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getSignalIcon = (signalType: string): string => {
    return signalType === 'BUY' ? '📈' : '📉';
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.9) return 'text-green-600 dark:text-green-400';
    if (confidence >= 0.8) return 'text-blue-600 dark:text-blue-400';
    if (confidence >= 0.7) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  const getAccessTierBadge = (tier?: string): React.ReactElement | null => {
    if (!tier || tier === 'free') return null;

    const colors = {
      premium: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      holder: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      whale: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    };

    return (
      <span
        className={`px-2 py-1 rounded-full text-xs font-medium ${
          colors[tier as keyof typeof colors] || ''
        }`}
      >
        {tier.toUpperCase()}
      </span>
    );
  };

  if (!connected) {
    return (
      <div className={`bg-gray-50 dark:bg-gray-800 rounded-lg p-6 text-center ${className}`}>
        <div className="text-gray-400 dark:text-gray-500 mb-2">🔌</div>
        <p className="text-gray-600 dark:text-gray-400">Connecting to real-time notifications...</p>
      </div>
    );
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">🚨 Live Signals</h3>
            {getAccessTierBadge(accessTier)}
            {unreadCount > 0 && (
              <span className="bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
                {unreadCount}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Filter */}
            <select
              value={filter}
              onChange={e => setFilter(e.target.value as 'all' | 'BUY' | 'SELL')}
              className="text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="all">All Signals</option>
              <option value="BUY">BUY Only</option>
              <option value="SELL">SELL Only</option>
            </select>

            {/* Expand/Collapse */}
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 text-sm"
            >
              {isExpanded ? 'Collapse' : 'Expand'}
            </button>
          </div>
        </div>

        {/* Connection Status */}
        <div className="flex items-center gap-4 mt-2 text-sm text-gray-600 dark:text-gray-400">
          <span className="flex items-center gap-1">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            Connected ({authType})
          </span>
          {unreadCount > 0 && (
            <button
              onClick={markAllAsRead}
              className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
            >
              Mark all as read
            </button>
          )}
        </div>
      </div>

      {/* Notifications List */}
      {isExpanded && (
        <div className="max-h-96 overflow-y-auto">
          {filteredNotifications.length === 0 ? (
            <div className="p-6 text-center text-gray-500 dark:text-gray-400">
              <div className="text-2xl mb-2">📭</div>
              <p>No signals yet. Waiting for trading opportunities...</p>
              <p className="text-sm mt-1">
                Connected to {authType} tier with {accessTier} access
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredNotifications.map((notification, index) => (
                <div
                  key={`${notification.data.signal_id}-${index}`}
                  className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors"
                  onClick={() => markAsRead(notification.data.signal_id)}
                >
                  <div className="flex items-start justify-between">
                    {/* Signal Info */}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-lg">
                          {getSignalIcon(notification.data.signal_type)}
                        </span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {notification.data.pair}
                        </span>
                        <span
                          className={`font-semibold ${
                            notification.data.signal_type === 'BUY'
                              ? 'text-green-600 dark:text-green-400'
                              : 'text-red-600 dark:text-red-400'
                          }`}
                        >
                          {notification.data.signal_type}
                        </span>
                        {notification.data.channel !== 'public' && (
                          <span className="text-xs bg-gray-100 dark:bg-gray-600 text-gray-600 dark:text-gray-300 px-2 py-1 rounded">
                            {notification.data.channel}
                          </span>
                        )}
                      </div>

                      <div className="grid grid-cols-2 gap-4 text-sm text-gray-600 dark:text-gray-400">
                        <div>
                          <span className="font-medium">Entry Price:</span>
                          <span className="ml-1 font-mono">
                            {formatPrice(notification.data.entry_price)}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium">Confidence:</span>
                          <span
                            className={`ml-1 font-semibold ${getConfidenceColor(
                              notification.data.confidence_score
                            )}`}
                          >
                            {formatConfidence(notification.data.confidence_score)}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Time */}
                    <div className="text-xs text-gray-500 dark:text-gray-400 ml-4">
                      {formatTime(notification.timestamp)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Summary */}
      {!isExpanded && notifications.length > 0 && (
        <div className="px-6 py-3 bg-gray-50 dark:bg-gray-700 text-sm text-gray-600 dark:text-gray-400">
          <div className="flex items-center justify-between">
            <span>
              {notifications.length} signal{notifications.length !== 1 ? 's' : ''} received
            </span>
            {unreadCount > 0 && (
              <span className="text-blue-600 dark:text-blue-400 font-medium">
                {unreadCount} unread
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Compact notification widget for dashboard
 */
export function NotificationWidget({ className = '' }: { className?: string }) {
  const { connected, unreadCount, notifications } = useNotificationConnection();
  const latestNotification = notifications[0];

  if (!connected) {
    return (
      <div className={`flex items-center gap-2 text-gray-500 dark:text-gray-400 ${className}`}>
        <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
        <span className="text-sm">Connecting...</span>
      </div>
    );
  }

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className="flex items-center gap-1">
        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
        <span className="text-sm text-gray-600 dark:text-gray-400">Live</span>
      </div>

      {unreadCount > 0 && (
        <div className="flex items-center gap-2">
          <span className="bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount}
          </span>
          {latestNotification && (
            <div className="text-sm">
              <span className="font-medium">{latestNotification.data.pair}</span>
              <span
                className={`ml-1 font-semibold ${
                  latestNotification.data.signal_type === 'BUY'
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400'
                }`}
              >
                {latestNotification.data.signal_type}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

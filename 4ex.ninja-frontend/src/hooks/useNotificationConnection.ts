/**
 * React Hook for Onchain Notification Manager
 * Day 3-4: Easy React integration for wallet-aware notifications
 */

'use client';

import {
  AccessTier,
  AuthType,
  onchainNotificationManager,
  OnchainNotificationPrefs,
  SignalNotification,
  WebSocketConnection,
} from '@/utils/onchain-notification-manager';
import { useSession } from 'next-auth/react';
import { useCallback, useEffect, useRef, useState } from 'react';

export interface UseNotificationConnection {
  // Connection state
  connected: boolean;
  authType?: AuthType;
  accessTier?: AccessTier;
  connectionCount: number;

  // Connection methods
  connectWithWallet: (walletAddress: string, signature?: string) => Promise<WebSocketConnection>;
  connectWithSession: (sessionToken: string, userId?: string) => Promise<WebSocketConnection>;
  connectAnonymous: (anonymousId?: string) => Promise<WebSocketConnection>;
  disconnect: () => void;

  // Notification management
  notifications: SignalNotification[];
  unreadCount: number;
  markAsRead: (signalId?: string) => void;
  markAllAsRead: () => void;

  // Preferences
  preferences: OnchainNotificationPrefs;
  updatePreferences: (updates: Partial<OnchainNotificationPrefs>) => void;

  // Subscription management
  subscribeToTokenGatedSignals: (tier: AccessTier) => void;

  // Error handling
  error: string | null;
  clearError: () => void;
}

export interface NotificationState {
  notification: SignalNotification;
  read: boolean;
  timestamp: Date;
}

export function useNotificationConnection(): UseNotificationConnection {
  const { data: session, status } = useSession();

  // Connection state
  const [connected, setConnected] = useState(false);
  const [authType, setAuthType] = useState<AuthType>();
  const [accessTier, setAccessTier] = useState<AccessTier>();
  const [connectionCount, setConnectionCount] = useState(0);

  // Notification state
  const [notifications, setNotifications] = useState<NotificationState[]>([]);
  const [preferences, setPreferences] = useState<OnchainNotificationPrefs>(() => {
    if (typeof window === 'undefined' || !onchainNotificationManager) {
      return {
        sounds: true,
        browserPush: false,
        signalTypes: ['BUY', 'SELL'],
        minimumConfidence: 0.7,
      };
    }
    return onchainNotificationManager.getPreferences();
  });
  const [error, setError] = useState<string | null>(null);

  // Refs for cleanup
  const notificationUnsubscribeRef = useRef<(() => void) | null>(null);
  const connectionUnsubscribeRef = useRef<(() => void) | null>(null);

  // Connection methods
  const connectWithWallet = useCallback(async (walletAddress: string, signature?: string) => {
    if (!onchainNotificationManager) {
      throw new Error('Notification manager not available');
    }

    try {
      setError(null);
      const connection = await onchainNotificationManager.connectWithWallet(
        walletAddress,
        signature
      );
      return connection;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to connect with wallet';
      setError(errorMessage);
      throw err;
    }
  }, []);

  const connectWithSession = useCallback(async (sessionToken: string, userId?: string) => {
    if (!onchainNotificationManager) {
      throw new Error('Notification manager not available');
    }

    try {
      setError(null);
      const connection = await onchainNotificationManager.connectWithSession(sessionToken, userId);
      return connection;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to connect with session';
      setError(errorMessage);
      throw err;
    }
  }, []);

  const connectAnonymous = useCallback(async (anonymousId?: string) => {
    if (!onchainNotificationManager) {
      throw new Error('Notification manager not available');
    }

    try {
      setError(null);
      const connection = await onchainNotificationManager.connectAnonymous(anonymousId);
      return connection;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to connect anonymously';
      setError(errorMessage);
      throw err;
    }
  }, []);

  const disconnect = useCallback(() => {
    if (onchainNotificationManager) {
      onchainNotificationManager.disconnect();
    }
  }, []);

  // Notification management
  const markAsRead = useCallback((signalId?: string) => {
    setNotifications(prev =>
      prev.map(notif =>
        !signalId || notif.notification.data.signal_id === signalId
          ? { ...notif, read: true }
          : notif
      )
    );
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications(prev => prev.map(notif => ({ ...notif, read: true })));
  }, []);

  // Preferences management
  const updatePreferences = useCallback((updates: Partial<OnchainNotificationPrefs>) => {
    if (onchainNotificationManager) {
      onchainNotificationManager.updatePreferences(updates);
      setPreferences(onchainNotificationManager.getPreferences());
    }
  }, []);

  // Subscription management
  const subscribeToTokenGatedSignals = useCallback((tier: AccessTier) => {
    if (onchainNotificationManager) {
      onchainNotificationManager.subscribeToTokenGatedSignals(tier);
    }
  }, []);

  // Error management
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Auto-connect based on session status
  useEffect(() => {
    if (status === 'loading') return;

    const initializeConnection = async () => {
      try {
        if (session?.user) {
          // Connect with session token for authenticated users
          const sessionToken = (session as any).accessToken || 'session_placeholder';
          const userId = (session as any).user?.id || session.user?.email || 'session_user';
          await connectWithSession(sessionToken, userId);
        } else {
          // Connect anonymously for unauthenticated users
          await connectAnonymous();
        }
      } catch (err) {
        console.warn('Failed to initialize notification connection:', err);
        // Don't set error state for auto-connection failures
      }
    };

    initializeConnection();
  }, [session, status, connectWithSession, connectAnonymous]);

  // Subscribe to notifications and connection changes
  useEffect(() => {
    if (!onchainNotificationManager) return;

    // Subscribe to notifications
    if (notificationUnsubscribeRef.current) {
      notificationUnsubscribeRef.current();
    }

    notificationUnsubscribeRef.current = onchainNotificationManager.onNotification(
      (notification: SignalNotification) => {
        setNotifications(prev => [
          {
            notification,
            read: false,
            timestamp: new Date(),
          },
          ...prev.slice(0, 99), // Keep last 100 notifications
        ]);
      }
    );

    // Subscribe to connection changes
    if (connectionUnsubscribeRef.current) {
      connectionUnsubscribeRef.current();
    }

    connectionUnsubscribeRef.current = onchainNotificationManager.onConnectionChange(
      (isConnected: boolean, connectionAuthType: AuthType) => {
        setConnected(isConnected);
        if (isConnected) {
          setAuthType(connectionAuthType);
          const status = onchainNotificationManager?.getConnectionStatus();
          if (status) {
            setAccessTier(status.accessTier);
            setConnectionCount(status.connectionCount);
          }
        } else {
          setAuthType(undefined);
          setAccessTier(undefined);
          setConnectionCount(0);
        }
      }
    );

    // Initial status update
    const status = onchainNotificationManager.getConnectionStatus();
    setConnected(status.connected);
    setAuthType(status.authType);
    setAccessTier(status.accessTier);
    setConnectionCount(status.connectionCount);

    // Cleanup on unmount
    return () => {
      if (notificationUnsubscribeRef.current) {
        notificationUnsubscribeRef.current();
      }
      if (connectionUnsubscribeRef.current) {
        connectionUnsubscribeRef.current();
      }
    };
  }, []);

  // Calculate unread count
  const unreadCount = notifications.filter(n => !n.read).length;

  return {
    // Connection state
    connected,
    authType,
    accessTier,
    connectionCount,

    // Connection methods
    connectWithWallet,
    connectWithSession,
    connectAnonymous,
    disconnect,

    // Notification management
    notifications: notifications.map(n => n.notification),
    unreadCount,
    markAsRead,
    markAllAsRead,

    // Preferences
    preferences,
    updatePreferences,

    // Subscription management
    subscribeToTokenGatedSignals,

    // Error handling
    error,
    clearError,
  };
}

/**
 * Hook for wallet connection with automatic WebSocket integration
 */
export function useWalletNotifications() {
  const { connectWithWallet, connected, authType, accessTier, error } = useNotificationConnection();
  const [walletAddress, setWalletAddress] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);

  const connectWallet = useCallback(
    async (address: string, signature?: string) => {
      setIsConnecting(true);
      try {
        await connectWithWallet(address, signature);
        setWalletAddress(address);
      } catch (err) {
        console.error('Wallet connection failed:', err);
        throw err;
      } finally {
        setIsConnecting(false);
      }
    },
    [connectWithWallet]
  );

  const isWalletConnected = connected && authType === 'wallet';

  return {
    walletAddress,
    isWalletConnected,
    isConnecting,
    accessTier,
    connectWallet,
    error,
  };
}

/**
 * Hook for notification preferences management
 */
export function useNotificationPreferences() {
  const { preferences, updatePreferences } = useNotificationConnection();

  const toggleSounds = useCallback(() => {
    updatePreferences({ sounds: !preferences.sounds });
  }, [preferences.sounds, updatePreferences]);

  const toggleBrowserPush = useCallback(() => {
    updatePreferences({ browserPush: !preferences.browserPush });
  }, [preferences.browserPush, updatePreferences]);

  const updateMinimumConfidence = useCallback(
    (confidence: number) => {
      updatePreferences({ minimumConfidence: confidence });
    },
    [updatePreferences]
  );

  const updateSignalTypes = useCallback(
    (signalTypes: string[]) => {
      updatePreferences({ signalTypes });
    },
    [updatePreferences]
  );

  return {
    preferences,
    toggleSounds,
    toggleBrowserPush,
    updateMinimumConfidence,
    updateSignalTypes,
    updatePreferences,
  };
}

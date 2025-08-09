'use client';

import { webSocketManager } from '@/utils/websocket-manager';
import { useCallback, useEffect, useRef, useState } from 'react';

export interface UseWebSocketOptions {
  url: string;
  protocols?: string | string[];
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  throttleMs?: number;
  autoConnect?: boolean;
  onOpen?: () => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (error: Event) => void;
  onMessage?: (data: any) => void;
}

export interface WebSocketState {
  isConnected: boolean;
  readyState: number;
  reconnectAttempts: number;
  lastMessage: any;
  connectionId: string | null;
}

/**
 * Enhanced WebSocket hook with connection pooling and performance optimizations
 */
export function useWebSocket(options: UseWebSocketOptions) {
  const {
    url,
    protocols,
    reconnectDelay = 1000,
    maxReconnectAttempts = 5,
    heartbeatInterval = 30000,
    throttleMs = 100,
    autoConnect = true,
    onOpen,
    onClose,
    onError,
    onMessage,
  } = options;

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    readyState: WebSocket.CLOSED,
    reconnectAttempts: 0,
    lastMessage: null,
    connectionId: null,
  });

  const unsubscribeRef = useRef<(() => void) | null>(null);
  const statusCheckIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isManualDisconnectRef = useRef(false);

  const updateConnectionStatus = useCallback(() => {
    if (state.connectionId) {
      const status = webSocketManager.getConnectionStatus(state.connectionId);
      setState(prev => ({
        ...prev,
        isConnected: status.isConnected,
        readyState: status.readyState,
        reconnectAttempts: status.reconnectAttempts,
      }));

      // Call event handlers based on state changes
      if (status.isConnected && !state.isConnected && onOpen) {
        onOpen();
      }
    }
  }, [state.connectionId, state.isConnected, onOpen]);

  const connect = useCallback(async () => {
    if (state.connectionId) {
      return; // Already connected or connecting
    }

    isManualDisconnectRef.current = false;

    try {
      const connectionId = await webSocketManager.getConnection({
        url,
        protocols,
        reconnectDelay,
        maxReconnectAttempts,
        heartbeatInterval,
        throttleMs,
      });

      setState(prev => ({
        ...prev,
        connectionId,
      }));

      // Subscribe to messages
      const unsubscribe = webSocketManager.subscribe(connectionId, data => {
        setState(prev => ({
          ...prev,
          lastMessage: data,
        }));

        if (onMessage) {
          onMessage(data);
        }
      });

      unsubscribeRef.current = unsubscribe;

      // Start periodic status checks
      statusCheckIntervalRef.current = setInterval(updateConnectionStatus, 1000);
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      if (onError) {
        onError(error as Event);
      }
    }
  }, [
    url,
    protocols,
    reconnectDelay,
    maxReconnectAttempts,
    heartbeatInterval,
    throttleMs,
    onMessage,
    onError,
    state.connectionId,
    updateConnectionStatus,
  ]);

  const disconnect = useCallback(() => {
    isManualDisconnectRef.current = true;

    if (statusCheckIntervalRef.current) {
      clearInterval(statusCheckIntervalRef.current);
      statusCheckIntervalRef.current = null;
    }

    if (unsubscribeRef.current) {
      unsubscribeRef.current();
      unsubscribeRef.current = null;
    }

    if (state.connectionId) {
      webSocketManager.closeConnection(state.connectionId);
      setState(prev => ({
        ...prev,
        connectionId: null,
        isConnected: false,
        readyState: WebSocket.CLOSED,
        reconnectAttempts: 0,
      }));

      if (onClose) {
        onClose({
          wasClean: true,
          code: 1000,
          reason: 'Manual disconnect',
        } as CloseEvent);
      }
    }
  }, [state.connectionId, onClose]);

  const sendMessage = useCallback(
    (message: any): boolean => {
      if (!state.connectionId) {
        console.warn('Cannot send message: WebSocket not connected');
        return false;
      }

      return webSocketManager.sendMessage(state.connectionId, message);
    },
    [state.connectionId]
  );

  const reconnect = useCallback(() => {
    disconnect();
    setTimeout(() => {
      if (!isManualDisconnectRef.current) {
        connect();
      }
    }, 100);
  }, [disconnect, connect]);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect]); // Only run on mount/unmount

  // Update status periodically
  useEffect(() => {
    updateConnectionStatus();
  }, [updateConnectionStatus]);

  return {
    // Connection state
    ...state,

    // Connection methods
    connect,
    disconnect,
    reconnect,
    sendMessage,

    // Utility methods
    getActiveConnections: () => webSocketManager.getActiveConnections(),

    // State helpers
    isConnecting: state.readyState === WebSocket.CONNECTING,
    isOpen: state.readyState === WebSocket.OPEN,
    isClosing: state.readyState === WebSocket.CLOSING,
    isClosed: state.readyState === WebSocket.CLOSED,
  };
}

/**
 * Simplified hook for basic WebSocket usage
 */
export function useSimpleWebSocket(url: string, onMessage?: (data: any) => void) {
  return useWebSocket({
    url,
    onMessage,
    autoConnect: true,
    throttleMs: 100,
  });
}

/**
 * Hook for high-frequency trading data with aggressive throttling
 */
export function useTradingWebSocket(url: string, onMessage?: (data: any) => void) {
  return useWebSocket({
    url,
    onMessage,
    autoConnect: true,
    throttleMs: 50, // More aggressive throttling for trading data
    heartbeatInterval: 10000, // More frequent heartbeat
    maxReconnectAttempts: 10, // More persistent reconnection
  });
}

/**
 * Hook for real-time notifications with lower frequency updates
 */
export function useNotificationWebSocket(url: string, onMessage?: (data: any) => void) {
  return useWebSocket({
    url,
    onMessage,
    autoConnect: true,
    throttleMs: 500, // Less frequent updates for notifications
    heartbeatInterval: 60000, // Less frequent heartbeat
  });
}

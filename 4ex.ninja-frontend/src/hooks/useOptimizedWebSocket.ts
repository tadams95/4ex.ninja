'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

interface WebSocketMessage {
  type: string;
  payload: any;
  requestId?: string;
}

interface WebSocketSubscription {
  type: string;
  symbol?: string;
  [key: string]: any;
}

interface UseWebSocketOptions {
  url: string;
  protocols?: string | string[];
  throttleMs?: number;
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
  onMessage?: (data: any) => void;
  onError?: (error: any) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  connectionId: string | null;
  reconnectAttempts: number;
}

/**
 * Optimized WebSocket hook that uses Web Workers for better performance
 * Includes connection pooling, throttling, and automatic reconnection
 */
export const useOptimizedWebSocket = (options: UseWebSocketOptions) => {
  const {
    url,
    protocols,
    throttleMs = 100, // Throttle messages to prevent excessive re-renders
    reconnectDelay = 1000,
    maxReconnectAttempts = 5,
    onMessage,
    onError,
    onConnect,
    onDisconnect,
  } = options;

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    connectionId: null,
    reconnectAttempts: 0,
  });

  const workerRef = useRef<Worker | null>(null);
  const requestIdRef = useRef(0);
  const subscriptionsRef = useRef<Set<string>>(new Set());
  const throttleRef = useRef<{ [key: string]: any }>({});
  const throttleTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const messageBufferRef = useRef<any[]>([]);

  // Generate unique request ID
  const generateRequestId = useCallback(() => {
    return `req_${++requestIdRef.current}`;
  }, []);

  // Throttled message processing to prevent excessive re-renders
  const throttledMessageHandler = useCallback(
    (data: any) => {
      // Add to buffer
      messageBufferRef.current.push(data);

      // Clear existing timeout
      if (throttleTimeoutRef.current) {
        clearTimeout(throttleTimeoutRef.current);
      }

      // Set new timeout for batch processing
      throttleTimeoutRef.current = setTimeout(() => {
        const messages = [...messageBufferRef.current];
        messageBufferRef.current = [];

        // Process messages in batch
        if (messages.length > 0 && onMessage) {
          // For real-time data, we usually want the latest values
          // Group messages by symbol/key and keep only the latest
          const latestMessages = messages.reduce((acc, msg) => {
            if (msg.data?.data) {
              // Handle Finnhub-style data structure
              msg.data.data.forEach((trade: any) => {
                acc[trade.s] = trade;
              });
            } else if (msg.data?.symbol) {
              // Handle generic symbol-based data
              acc[msg.data.symbol] = msg.data;
            } else {
              // Handle other message types
              acc[`${msg.type}_${Date.now()}`] = msg.data;
            }
            return acc;
          }, {} as { [key: string]: any });

          // Call onMessage with processed data
          onMessage(Object.values(latestMessages));
        }
      }, throttleMs);
    },
    [onMessage, throttleMs]
  );

  // Initialize Web Worker
  useEffect(() => {
    try {
      // Create worker from public directory
      workerRef.current = new Worker('/websocket-worker.js');

      // Setup message handler
      workerRef.current.onmessage = (event: MessageEvent<WebSocketMessage>) => {
        const { type, payload, requestId } = event.data;

        switch (type) {
          case 'CONNECTION_OPENED':
            setState(prev => ({
              ...prev,
              isConnected: true,
              isConnecting: false,
              error: null,
              connectionId: payload.connectionId,
              reconnectAttempts: 0,
            }));
            onConnect?.();
            break;

          case 'CONNECTION_CLOSED':
            setState(prev => ({
              ...prev,
              isConnected: false,
              isConnecting: false,
            }));
            onDisconnect?.();
            break;

          case 'CONNECTION_ERROR':
            setState(prev => ({
              ...prev,
              isConnected: false,
              isConnecting: false,
              error: payload.error,
            }));
            onError?.(payload.error);
            break;

          case 'MESSAGE_RECEIVED':
            throttledMessageHandler(payload);
            break;

          case 'RECONNECTION_ATTEMPT':
            setState(prev => ({
              ...prev,
              reconnectAttempts: payload.attempt,
              isConnecting: true,
            }));
            break;

          case 'WORKER_ERROR':
            console.error('WebSocket Worker Error:', payload.error);
            onError?.(payload.error);
            break;

          default:
            console.log('Unknown message type from worker:', type);
        }
      };

      // Handle worker errors
      workerRef.current.onerror = error => {
        console.error('WebSocket Worker Error:', error);
        onError?.(error.message);
      };

      return () => {
        if (workerRef.current) {
          // Cleanup connections before terminating worker
          workerRef.current.postMessage({
            type: 'CLEANUP',
            payload: {},
            id: generateRequestId(),
          });

          // Small delay to allow cleanup, then terminate
          setTimeout(() => {
            workerRef.current?.terminate();
          }, 100);
        }

        // Clear throttle timeout
        if (throttleTimeoutRef.current) {
          clearTimeout(throttleTimeoutRef.current);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket worker:', error);
      onError?.(error instanceof Error ? error.message : 'Worker creation failed');
    }
  }, [generateRequestId, onConnect, onDisconnect, onError, throttledMessageHandler]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!workerRef.current || state.isConnecting || state.isConnected) {
      return;
    }

    setState(prev => ({ ...prev, isConnecting: true, error: null }));

    workerRef.current.postMessage({
      type: 'CONNECT',
      payload: {
        url,
        protocols,
        options: {
          reconnectDelay,
          maxReconnectAttempts,
        },
      },
      id: generateRequestId(),
    });
  }, [
    url,
    protocols,
    reconnectDelay,
    maxReconnectAttempts,
    generateRequestId,
    state.isConnecting,
    state.isConnected,
  ]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (!workerRef.current || !state.connectionId) {
      return;
    }

    workerRef.current.postMessage({
      type: 'DISCONNECT',
      payload: {
        connectionId: state.connectionId,
      },
      id: generateRequestId(),
    });

    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
      connectionId: null,
    }));
  }, [state.connectionId, generateRequestId]);

  // Subscribe to symbols/topics
  const subscribe = useCallback(
    (subscription: WebSocketSubscription) => {
      if (!workerRef.current || !state.connectionId || !state.isConnected) {
        console.warn('Cannot subscribe: WebSocket not connected');
        return;
      }

      const subscriptionKey = JSON.stringify(subscription);
      if (subscriptionsRef.current.has(subscriptionKey)) {
        return; // Already subscribed
      }

      subscriptionsRef.current.add(subscriptionKey);

      workerRef.current.postMessage({
        type: 'SUBSCRIBE',
        payload: {
          connectionId: state.connectionId,
          subscription,
        },
        id: generateRequestId(),
      });
    },
    [state.connectionId, state.isConnected, generateRequestId]
  );

  // Unsubscribe from symbols/topics
  const unsubscribe = useCallback(
    (subscription: WebSocketSubscription) => {
      if (!workerRef.current || !state.connectionId) {
        return;
      }

      const subscriptionKey = JSON.stringify(subscription);
      subscriptionsRef.current.delete(subscriptionKey);

      workerRef.current.postMessage({
        type: 'UNSUBSCRIBE',
        payload: {
          connectionId: state.connectionId,
          subscription,
        },
        id: generateRequestId(),
      });
    },
    [state.connectionId, generateRequestId]
  );

  // Auto-connect on mount
  useEffect(() => {
    connect();
  }, [connect]);

  // Cleanup subscriptions on unmount
  useEffect(() => {
    return () => {
      subscriptionsRef.current.clear();
    };
  }, []);

  return {
    ...state,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
  };
};

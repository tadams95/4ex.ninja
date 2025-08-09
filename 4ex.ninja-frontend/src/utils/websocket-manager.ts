'use client';

/**
 * WebSocket Connection Manager
 * Provides connection pooling, automatic reconnection, and message throttling
 * for optimal real-time data handling across the application
 */

interface WebSocketConfig {
  url: string;
  protocols?: string | string[];
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  throttleMs?: number;
}

interface ConnectionInfo {
  id: string;
  url: string;
  readyState: number;
  subscriptions: Set<string>;
  lastActivity: number;
  reconnectAttempts: number;
}

export class WebSocketConnectionManager {
  private static instance: WebSocketConnectionManager;
  private connections: Map<string, WebSocket> = new Map();
  private connectionInfo: Map<string, ConnectionInfo> = new Map();
  private messageHandlers: Map<string, Set<(data: any) => void>> = new Map();
  private throttleTimers: Map<string, NodeJS.Timeout> = new Map();
  private messageBuffers: Map<string, any[]> = new Map();
  private reconnectTimers: Map<string, NodeJS.Timeout> = new Map();

  private constructor() {
    // Singleton pattern
    if (typeof window !== 'undefined') {
      // Cleanup on page unload
      window.addEventListener('beforeunload', () => {
        this.cleanup();
      });
    }
  }

  public static getInstance(): WebSocketConnectionManager {
    if (!WebSocketConnectionManager.instance) {
      WebSocketConnectionManager.instance = new WebSocketConnectionManager();
    }
    return WebSocketConnectionManager.instance;
  }

  /**
   * Get or create a WebSocket connection
   */
  public async getConnection(config: WebSocketConfig): Promise<string> {
    const connectionId = this.generateConnectionId(config.url);

    // Return existing connection if available
    if (this.connections.has(connectionId)) {
      const connection = this.connections.get(connectionId)!;
      if (connection.readyState === WebSocket.OPEN) {
        return connectionId;
      }
    }

    // Create new connection
    return this.createConnection(connectionId, config);
  }

  /**
   * Subscribe to messages from a specific connection
   */
  public subscribe(connectionId: string, handler: (data: any) => void): () => void {
    if (!this.messageHandlers.has(connectionId)) {
      this.messageHandlers.set(connectionId, new Set());
    }

    this.messageHandlers.get(connectionId)!.add(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.messageHandlers.get(connectionId);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          this.messageHandlers.delete(connectionId);
        }
      }
    };
  }

  /**
   * Send message through a connection
   */
  public sendMessage(connectionId: string, message: any): boolean {
    const connection = this.connections.get(connectionId);
    if (!connection || connection.readyState !== WebSocket.OPEN) {
      return false;
    }

    try {
      const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
      connection.send(messageStr);

      // Update activity timestamp
      const info = this.connectionInfo.get(connectionId);
      if (info) {
        info.lastActivity = Date.now();
      }

      return true;
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
      return false;
    }
  }

  /**
   * Close a specific connection
   */
  public closeConnection(connectionId: string): void {
    const connection = this.connections.get(connectionId);
    if (connection) {
      connection.close();
    }

    this.cleanupConnection(connectionId);
  }

  /**
   * Get connection status
   */
  public getConnectionStatus(connectionId: string): {
    isConnected: boolean;
    readyState: number;
    reconnectAttempts: number;
  } {
    const connection = this.connections.get(connectionId);
    const info = this.connectionInfo.get(connectionId);

    return {
      isConnected: connection?.readyState === WebSocket.OPEN || false,
      readyState: connection?.readyState || WebSocket.CLOSED,
      reconnectAttempts: info?.reconnectAttempts || 0,
    };
  }

  /**
   * List all active connections
   */
  public getActiveConnections(): ConnectionInfo[] {
    return Array.from(this.connectionInfo.values());
  }

  /**
   * Cleanup all connections
   */
  public cleanup(): void {
    // Clear all timers
    this.throttleTimers.forEach(timer => clearTimeout(timer));
    this.reconnectTimers.forEach(timer => clearTimeout(timer));

    // Close all connections
    this.connections.forEach((connection, id) => {
      if (
        connection.readyState === WebSocket.OPEN ||
        connection.readyState === WebSocket.CONNECTING
      ) {
        connection.close();
      }
    });

    // Clear all maps
    this.connections.clear();
    this.connectionInfo.clear();
    this.messageHandlers.clear();
    this.throttleTimers.clear();
    this.messageBuffers.clear();
    this.reconnectTimers.clear();
  }

  private async createConnection(connectionId: string, config: WebSocketConfig): Promise<string> {
    return new Promise((resolve, reject) => {
      try {
        const socket = new WebSocket(config.url, config.protocols);

        const info: ConnectionInfo = {
          id: connectionId,
          url: config.url,
          readyState: socket.readyState,
          subscriptions: new Set(),
          lastActivity: Date.now(),
          reconnectAttempts: 0,
        };

        this.connections.set(connectionId, socket);
        this.connectionInfo.set(connectionId, info);

        socket.onopen = () => {
          info.readyState = socket.readyState;
          info.reconnectAttempts = 0;
          console.log(`WebSocket connected: ${connectionId}`);
          resolve(connectionId);
        };

        socket.onmessage = event => {
          info.lastActivity = Date.now();
          this.handleMessage(connectionId, event.data, config.throttleMs || 100);
        };

        socket.onerror = error => {
          console.error(`WebSocket error (${connectionId}):`, error);
          if (socket.readyState === WebSocket.CONNECTING) {
            reject(error);
          }
        };

        socket.onclose = event => {
          info.readyState = socket.readyState;
          console.log(`WebSocket closed: ${connectionId}`, event.code, event.reason);

          // Attempt reconnection if not a clean close
          if (!event.wasClean && info.reconnectAttempts < (config.maxReconnectAttempts || 5)) {
            this.scheduleReconnection(connectionId, config);
          } else {
            this.cleanupConnection(connectionId);
          }
        };

        // Set up heartbeat if configured
        if (config.heartbeatInterval) {
          this.setupHeartbeat(connectionId, config.heartbeatInterval);
        }
      } catch (error) {
        reject(error);
      }
    });
  }

  private handleMessage(connectionId: string, data: string, throttleMs: number): void {
    try {
      const parsedData = JSON.parse(data);

      // Add to buffer
      if (!this.messageBuffers.has(connectionId)) {
        this.messageBuffers.set(connectionId, []);
      }
      this.messageBuffers.get(connectionId)!.push(parsedData);

      // Clear existing timer
      const existingTimer = this.throttleTimers.get(connectionId);
      if (existingTimer) {
        clearTimeout(existingTimer);
      }

      // Set new throttled processing timer
      const timer = setTimeout(() => {
        const buffer = this.messageBuffers.get(connectionId) || [];
        this.messageBuffers.set(connectionId, []);

        if (buffer.length > 0) {
          const handlers = this.messageHandlers.get(connectionId);
          if (handlers) {
            handlers.forEach(handler => {
              try {
                // For real-time data, we often want the latest values
                // You can customize this logic based on your needs
                handler(buffer);
              } catch (error) {
                console.error('Error in message handler:', error);
              }
            });
          }
        }
      }, throttleMs);

      this.throttleTimers.set(connectionId, timer);
    } catch (error) {
      // Handle non-JSON messages
      const handlers = this.messageHandlers.get(connectionId);
      if (handlers) {
        handlers.forEach(handler => {
          try {
            handler(data);
          } catch (handlerError) {
            console.error('Error in message handler:', handlerError);
          }
        });
      }
    }
  }

  private scheduleReconnection(connectionId: string, config: WebSocketConfig): void {
    const info = this.connectionInfo.get(connectionId);
    if (!info) return;

    info.reconnectAttempts++;
    const delay = (config.reconnectDelay || 1000) * Math.pow(2, info.reconnectAttempts - 1);

    console.log(
      `Scheduling reconnection for ${connectionId} in ${delay}ms (attempt ${info.reconnectAttempts})`
    );

    const timer = setTimeout(async () => {
      try {
        await this.createConnection(connectionId, config);
      } catch (error) {
        console.error(`Reconnection failed for ${connectionId}:`, error);
      }
    }, delay);

    this.reconnectTimers.set(connectionId, timer);
  }

  private setupHeartbeat(connectionId: string, interval: number): void {
    const heartbeatTimer = setInterval(() => {
      const connection = this.connections.get(connectionId);
      const info = this.connectionInfo.get(connectionId);

      if (!connection || !info) {
        clearInterval(heartbeatTimer);
        return;
      }

      if (connection.readyState === WebSocket.OPEN) {
        const timeSinceLastActivity = Date.now() - info.lastActivity;

        if (timeSinceLastActivity > interval * 2) {
          // Connection seems stale
          console.log(`Heartbeat timeout for ${connectionId}, closing connection`);
          connection.close();
        } else {
          // Send ping
          try {
            connection.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
          } catch (error) {
            // Ignore ping errors
          }
        }
      } else {
        clearInterval(heartbeatTimer);
      }
    }, interval);
  }

  private cleanupConnection(connectionId: string): void {
    // Clear timers
    const throttleTimer = this.throttleTimers.get(connectionId);
    if (throttleTimer) {
      clearTimeout(throttleTimer);
      this.throttleTimers.delete(connectionId);
    }

    const reconnectTimer = this.reconnectTimers.get(connectionId);
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      this.reconnectTimers.delete(connectionId);
    }

    // Remove from maps
    this.connections.delete(connectionId);
    this.connectionInfo.delete(connectionId);
    this.messageHandlers.delete(connectionId);
    this.messageBuffers.delete(connectionId);
  }

  private generateConnectionId(url: string): string {
    // Create a deterministic ID based on URL so same URLs reuse connections
    const urlHash = btoa(url)
      .replace(/[^a-zA-Z0-9]/g, '')
      .substring(0, 10);
    return `ws_${urlHash}`;
  }
}

// Export singleton instance
export const webSocketManager = WebSocketConnectionManager.getInstance();

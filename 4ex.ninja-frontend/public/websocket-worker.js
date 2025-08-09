// Web Worker for handling WebSocket connections
// This moves WebSocket processing off the main thread for better performance

class WebSocketWorkerManager {
  constructor() {
    this.connections = new Map(); // Connection pool
    this.subscriptions = new Map(); // Track subscriptions per connection
    this.reconnectTimeouts = new Map(); // Track reconnection attempts
    this.messageQueues = new Map(); // Buffer messages during reconnection

    // Configuration
    this.maxConnections = 3;
    this.reconnectDelay = 1000;
    this.maxReconnectAttempts = 5;
    this.heartbeatInterval = 30000; // 30 seconds

    this.setupMessageHandling();
  }

  setupMessageHandling() {
    self.addEventListener('message', event => {
      const { type, payload, id } = event.data;

      switch (type) {
        case 'CONNECT':
          this.handleConnect(payload, id);
          break;
        case 'SUBSCRIBE':
          this.handleSubscribe(payload, id);
          break;
        case 'UNSUBSCRIBE':
          this.handleUnsubscribe(payload, id);
          break;
        case 'DISCONNECT':
          this.handleDisconnect(payload, id);
          break;
        case 'CLEANUP':
          this.handleCleanup();
          break;
        default:
          console.warn('Unknown message type:', type);
      }
    });
  }

  handleConnect({ url, protocols, options = {} }, requestId) {
    try {
      // Check if we already have a connection to this URL
      const existingConnection = this.findConnectionByUrl(url);
      if (existingConnection) {
        this.sendMessage({
          type: 'CONNECTION_REUSED',
          payload: { connectionId: existingConnection.id, url },
          requestId,
        });
        return;
      }

      // Check connection limit
      if (this.connections.size >= this.maxConnections) {
        this.sendMessage({
          type: 'CONNECTION_ERROR',
          payload: { error: 'Maximum connections reached', url },
          requestId,
        });
        return;
      }

      const connectionId = this.generateConnectionId();
      const socket = new WebSocket(url, protocols);

      const connection = {
        id: connectionId,
        socket,
        url,
        subscriptions: new Set(),
        lastActivity: Date.now(),
        reconnectAttempts: 0,
        isConnecting: true,
        ...options,
      };

      this.connections.set(connectionId, connection);
      this.setupSocketEventHandlers(connection, requestId);
    } catch (error) {
      this.sendMessage({
        type: 'CONNECTION_ERROR',
        payload: { error: error.message, url },
        requestId,
      });
    }
  }

  setupSocketEventHandlers(connection, requestId) {
    const { socket, id: connectionId } = connection;

    socket.onopen = () => {
      connection.isConnecting = false;
      connection.reconnectAttempts = 0;

      // Send queued messages if any
      const queue = this.messageQueues.get(connectionId);
      if (queue && queue.length > 0) {
        queue.forEach(message => socket.send(message));
        this.messageQueues.delete(connectionId);
      }

      this.sendMessage({
        type: 'CONNECTION_OPENED',
        payload: { connectionId, url: connection.url },
        requestId,
      });

      // Setup heartbeat
      this.setupHeartbeat(connection);
    };

    socket.onmessage = event => {
      connection.lastActivity = Date.now();

      try {
        const data = JSON.parse(event.data);
        this.sendMessage({
          type: 'MESSAGE_RECEIVED',
          payload: { connectionId, data, timestamp: Date.now() },
        });
      } catch (error) {
        // Handle non-JSON messages
        this.sendMessage({
          type: 'MESSAGE_RECEIVED',
          payload: { connectionId, data: event.data, timestamp: Date.now() },
        });
      }
    };

    socket.onerror = error => {
      this.sendMessage({
        type: 'CONNECTION_ERROR',
        payload: { connectionId, error: error.message || 'WebSocket error' },
      });
    };

    socket.onclose = event => {
      connection.isConnecting = false;

      this.sendMessage({
        type: 'CONNECTION_CLOSED',
        payload: {
          connectionId,
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean,
        },
      });

      // Attempt reconnection if it wasn't a clean close
      if (!event.wasClean && connection.reconnectAttempts < this.maxReconnectAttempts) {
        this.scheduleReconnection(connection);
      } else {
        this.cleanupConnection(connectionId);
      }
    };
  }

  setupHeartbeat(connection) {
    const heartbeatId = setInterval(() => {
      if (connection.socket.readyState === WebSocket.OPEN) {
        const timeSinceLastActivity = Date.now() - connection.lastActivity;

        if (timeSinceLastActivity > this.heartbeatInterval * 2) {
          // Connection seems stale, close it
          connection.socket.close();
        } else {
          // Send ping if supported
          try {
            connection.socket.send(JSON.stringify({ type: 'ping' }));
          } catch (error) {
            // Ignore ping errors
          }
        }
      } else {
        clearInterval(heartbeatId);
      }
    }, this.heartbeatInterval);

    connection.heartbeatId = heartbeatId;
  }

  scheduleReconnection(connection) {
    const delay = this.reconnectDelay * Math.pow(2, connection.reconnectAttempts);

    const timeoutId = setTimeout(() => {
      if (this.connections.has(connection.id)) {
        connection.reconnectAttempts++;

        // Create new WebSocket instance
        const newSocket = new WebSocket(connection.url);
        connection.socket = newSocket;
        connection.isConnecting = true;

        this.setupSocketEventHandlers(connection);

        this.sendMessage({
          type: 'RECONNECTION_ATTEMPT',
          payload: {
            connectionId: connection.id,
            attempt: connection.reconnectAttempts,
            delay,
          },
        });
      }
    }, delay);

    this.reconnectTimeouts.set(connection.id, timeoutId);
  }

  handleSubscribe({ connectionId, subscription }, requestId) {
    const connection = this.connections.get(connectionId);

    if (!connection) {
      this.sendMessage({
        type: 'SUBSCRIPTION_ERROR',
        payload: { error: 'Connection not found', connectionId },
        requestId,
      });
      return;
    }

    if (connection.socket.readyState === WebSocket.OPEN) {
      try {
        const message = JSON.stringify(subscription);
        connection.socket.send(message);
        connection.subscriptions.add(JSON.stringify(subscription));

        this.sendMessage({
          type: 'SUBSCRIBED',
          payload: { connectionId, subscription },
          requestId,
        });
      } catch (error) {
        this.sendMessage({
          type: 'SUBSCRIPTION_ERROR',
          payload: { error: error.message, connectionId },
          requestId,
        });
      }
    } else {
      // Queue the subscription for when connection is ready
      if (!this.messageQueues.has(connectionId)) {
        this.messageQueues.set(connectionId, []);
      }
      this.messageQueues.get(connectionId).push(JSON.stringify(subscription));
    }
  }

  handleUnsubscribe({ connectionId, subscription }, requestId) {
    const connection = this.connections.get(connectionId);

    if (!connection) {
      this.sendMessage({
        type: 'UNSUBSCRIPTION_ERROR',
        payload: { error: 'Connection not found', connectionId },
        requestId,
      });
      return;
    }

    if (connection.socket.readyState === WebSocket.OPEN) {
      try {
        const message = JSON.stringify(subscription);
        connection.socket.send(message);
        connection.subscriptions.delete(JSON.stringify(subscription));

        this.sendMessage({
          type: 'UNSUBSCRIBED',
          payload: { connectionId, subscription },
          requestId,
        });
      } catch (error) {
        this.sendMessage({
          type: 'UNSUBSCRIPTION_ERROR',
          payload: { error: error.message, connectionId },
          requestId,
        });
      }
    }
  }

  handleDisconnect({ connectionId }, requestId) {
    this.cleanupConnection(connectionId);

    this.sendMessage({
      type: 'DISCONNECTED',
      payload: { connectionId },
      requestId,
    });
  }

  handleCleanup() {
    // Clean up all connections
    for (const [connectionId] of this.connections) {
      this.cleanupConnection(connectionId);
    }

    this.sendMessage({
      type: 'CLEANUP_COMPLETE',
      payload: {},
    });
  }

  cleanupConnection(connectionId) {
    const connection = this.connections.get(connectionId);

    if (connection) {
      // Clear heartbeat
      if (connection.heartbeatId) {
        clearInterval(connection.heartbeatId);
      }

      // Clear reconnection timeout
      const timeoutId = this.reconnectTimeouts.get(connectionId);
      if (timeoutId) {
        clearTimeout(timeoutId);
        this.reconnectTimeouts.delete(connectionId);
      }

      // Close socket if still open
      if (
        connection.socket.readyState === WebSocket.OPEN ||
        connection.socket.readyState === WebSocket.CONNECTING
      ) {
        connection.socket.close();
      }

      // Remove from maps
      this.connections.delete(connectionId);
      this.messageQueues.delete(connectionId);
    }
  }

  findConnectionByUrl(url) {
    for (const [id, connection] of this.connections) {
      if (connection.url === url) {
        return connection;
      }
    }
    return null;
  }

  generateConnectionId() {
    return `ws_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  sendMessage(message) {
    self.postMessage(message);
  }
}

// Initialize the worker manager
const wsManager = new WebSocketWorkerManager();

// Keep the worker alive
self.addEventListener('error', error => {
  self.postMessage({
    type: 'WORKER_ERROR',
    payload: { error: error.message, filename: error.filename, lineno: error.lineno },
  });
});

// Handle unhandled promise rejections
self.addEventListener('unhandledrejection', event => {
  self.postMessage({
    type: 'WORKER_ERROR',
    payload: { error: event.reason.toString() },
  });
});

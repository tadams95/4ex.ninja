/**
 * Onchain-Aware WebSocket Notification Manager
 * Day 3-4: Client-side wallet integration for notifications
 *
 * Features:
 * - Multi-auth support (wallet, session, anonymous)
 * - Token-gated notification channels
 * - Local preference storage with onchain migration readiness
 * - Real-time token balance monitoring
 * - Browser push notifications with wallet-based targeting
 */

'use client';

import { webSocketManager } from './websocket-manager';

// Notification channel access tiers
export const NOTIFICATION_TIERS = {
  public: [], // Free signals for everyone
  holders: ['premium_signals'], // Token holder exclusive
  premium: ['whale_signals'], // High-value signals
  whale: ['alpha_signals'], // Ultra-premium for large holders
} as const;

export interface OnchainNotificationPrefs {
  walletAddress?: string;
  sounds: boolean;
  browserPush: boolean;
  signalTypes: string[];
  minimumConfidence: number;
  // Future: stored onchain via smart contract
  tokenBalance?: bigint;
  accessTier?: AccessTier;
}

export type AccessTier = 'free' | 'premium' | 'holder' | 'whale';
export type AuthType = 'wallet' | 'session' | 'anonymous';

export interface NotificationChannel {
  id: string;
  name: string;
  description: string;
  accessTier: AccessTier;
  requiredTokenBalance?: bigint;
}

export interface WebSocketConnection {
  connectionId: string;
  authType: AuthType;
  accessTier: AccessTier;
  channels: string[];
  connected: boolean;
  reconnectAttempts: number;
}

export interface SignalNotification {
  type: 'signal';
  data: {
    signal_id: string;
    pair: string;
    signal_type: 'BUY' | 'SELL';
    entry_price: number;
    confidence_score: number;
    timestamp: string;
    channel: string;
  };
  timestamp: string;
}

export class OnchainNotificationManager {
  private static instance: OnchainNotificationManager;

  private connections: Map<string, WebSocketConnection> = new Map();
  private preferences: OnchainNotificationPrefs = {
    sounds: true,
    browserPush: false,
    signalTypes: ['BUY', 'SELL'],
    minimumConfidence: 0.7,
  };
  private messageHandlers: Set<(notification: SignalNotification) => void> = new Set();
  private connectionHandlers: Set<(connected: boolean, authType: AuthType) => void> = new Set();

  // WebSocket endpoints (configurable based on environment)
  private readonly WS_BASE_URL =
    process.env.NODE_ENV === 'production' ? 'wss://api.4ex.ninja' : 'ws://localhost:8000';

  private constructor() {
    this.loadPreferences();
    this.setupBrowserNotifications();
  }

  public static getInstance(): OnchainNotificationManager {
    if (!OnchainNotificationManager.instance) {
      OnchainNotificationManager.instance = new OnchainNotificationManager();
    }
    return OnchainNotificationManager.instance;
  }

  /**
   * Connect with wallet address for token-gated notifications
   */
  async connectWithWallet(walletAddress: string, signature?: string): Promise<WebSocketConnection> {
    const url = `${this.WS_BASE_URL}/ws/notifications?walletAddress=${walletAddress}`;
    if (signature) {
      // TODO: Add signature verification when wallet auth is fully implemented
    }

    const connectionId = await webSocketManager.getConnection({
      url,
      reconnectDelay: 1000,
      maxReconnectAttempts: 5,
      heartbeatInterval: 30000,
      throttleMs: 100,
    });

    // Simulate token balance check (will be real onchain call later)
    const tokenBalance = await this.getTokenBalance(walletAddress);
    const accessTier = this.calculateAccessTier(tokenBalance);

    const connection: WebSocketConnection = {
      connectionId,
      authType: 'wallet',
      accessTier,
      channels: this.getAvailableChannels(tokenBalance).map(ch => ch.id),
      connected: true,
      reconnectAttempts: 0,
    };

    this.connections.set(connectionId, connection);
    this.updatePreferences({ walletAddress, tokenBalance, accessTier });

    // Subscribe to messages
    webSocketManager.subscribe(connectionId, this.handleMessage.bind(this));

    // Notify connection handlers
    this.connectionHandlers.forEach(handler => handler(true, 'wallet'));

    console.log(`✅ Wallet connected: ${walletAddress} (${accessTier} tier)`);
    return connection;
  }

  /**
   * Connect with session token (current NextAuth.js users)
   */
  async connectWithSession(sessionToken: string, userId?: string): Promise<WebSocketConnection> {
    const url = `${this.WS_BASE_URL}/ws/notifications?sessionToken=${sessionToken}`;

    const connectionId = await webSocketManager.getConnection({
      url,
      reconnectDelay: 1000,
      maxReconnectAttempts: 5,
      heartbeatInterval: 30000,
      throttleMs: 100,
    });

    const connection: WebSocketConnection = {
      connectionId,
      authType: 'session',
      accessTier: 'premium', // Session users get premium access
      channels: ['public', 'premium'],
      connected: true,
      reconnectAttempts: 0,
    };

    this.connections.set(connectionId, connection);
    this.updatePreferences({ accessTier: 'premium' });

    // Subscribe to messages
    webSocketManager.subscribe(connectionId, this.handleMessage.bind(this));

    // Notify connection handlers
    this.connectionHandlers.forEach(handler => handler(true, 'session'));

    console.log(`✅ Session connected: ${userId || 'user'} (premium tier)`);
    return connection;
  }

  /**
   * Connect anonymously for public signals only
   */
  async connectAnonymous(anonymousId?: string): Promise<WebSocketConnection> {
    const finalId = anonymousId || this.generateAnonymousId();
    const url = `${this.WS_BASE_URL}/ws/notifications?anonymousId=${finalId}`;

    const connectionId = await webSocketManager.getConnection({
      url,
      reconnectDelay: 1000,
      maxReconnectAttempts: 3, // Fewer retries for anonymous
      heartbeatInterval: 60000, // Less frequent heartbeat
      throttleMs: 200,
    });

    const connection: WebSocketConnection = {
      connectionId,
      authType: 'anonymous',
      accessTier: 'free',
      channels: ['public'],
      connected: true,
      reconnectAttempts: 0,
    };

    this.connections.set(connectionId, connection);
    this.updatePreferences({ accessTier: 'free' });

    // Subscribe to messages
    webSocketManager.subscribe(connectionId, this.handleMessage.bind(this));

    // Notify connection handlers
    this.connectionHandlers.forEach(handler => handler(true, 'anonymous'));

    console.log(`✅ Anonymous connected: ${finalId} (free tier)`);
    return connection;
  }

  /**
   * Get available notification channels based on token balance
   */
  getAvailableChannels(tokenBalance: bigint): NotificationChannel[] {
    const channels: NotificationChannel[] = [
      {
        id: 'public',
        name: 'Public Signals',
        description: 'Basic trading signals available to everyone',
        accessTier: 'free',
      },
    ];

    // Add premium channels based on token balance
    if (tokenBalance >= BigInt(1000)) {
      // 1,000 tokens for premium
      channels.push({
        id: 'premium',
        name: 'Premium Signals',
        description: 'High-confidence signals for token holders',
        accessTier: 'premium',
        requiredTokenBalance: BigInt(1000),
      });
    }

    if (tokenBalance >= BigInt(10000)) {
      // 10,000 tokens for holder tier
      channels.push({
        id: 'holder',
        name: 'Holder Exclusive',
        description: 'Exclusive signals for significant token holders',
        accessTier: 'holder',
        requiredTokenBalance: BigInt(10000),
      });
    }

    if (tokenBalance >= BigInt(100000)) {
      // 100,000 tokens for whale tier
      channels.push({
        id: 'whale',
        name: 'Whale Alpha',
        description: 'Ultra-premium alpha signals for whale holders',
        accessTier: 'whale',
        requiredTokenBalance: BigInt(100000),
      });
    }

    return channels;
  }

  /**
   * Subscribe to token-gated signals based on access tier
   */
  subscribeToTokenGatedSignals(tier: AccessTier): void {
    const connections = Array.from(this.connections.values());

    connections.forEach(connection => {
      if (this.canAccessTier(connection.accessTier, tier)) {
        const message = {
          type: 'subscribe',
          channel: tier,
          timestamp: new Date().toISOString(),
        };

        webSocketManager.sendMessage(connection.connectionId, message);
        console.log(`📡 Subscribed to ${tier} signals`);
      } else {
        console.warn(`❌ Access denied for ${tier} tier (current: ${connection.accessTier})`);
      }
    });
  }

  /**
   * Update notification preferences
   */
  updatePreferences(updates: Partial<OnchainNotificationPrefs>): void {
    this.preferences = { ...this.preferences, ...updates };
    this.savePreferences();

    // Apply sound settings
    if (updates.sounds !== undefined) {
      this.configureSounds(updates.sounds);
    }

    // Apply browser push settings
    if (updates.browserPush !== undefined) {
      this.configureBrowserPush(updates.browserPush);
    }
  }

  /**
   * Get current preferences
   */
  getPreferences(): OnchainNotificationPrefs {
    return { ...this.preferences };
  }

  /**
   * Subscribe to notification messages
   */
  onNotification(handler: (notification: SignalNotification) => void): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  /**
   * Subscribe to connection status changes
   */
  onConnectionChange(handler: (connected: boolean, authType: AuthType) => void): () => void {
    this.connectionHandlers.add(handler);
    return () => this.connectionHandlers.delete(handler);
  }

  /**
   * Disconnect all WebSocket connections
   */
  disconnect(): void {
    this.connections.forEach(connection => {
      webSocketManager.closeConnection(connection.connectionId);
    });
    this.connections.clear();

    // Notify handlers
    this.connectionHandlers.forEach(handler => handler(false, 'anonymous'));
    console.log('🔌 All connections disconnected');
  }

  /**
   * Get connection status
   */
  getConnectionStatus(): {
    connected: boolean;
    authType?: AuthType;
    accessTier?: AccessTier;
    connectionCount: number;
  } {
    const connections = Array.from(this.connections.values());
    const activeConnections = connections.filter(c => c.connected);

    if (activeConnections.length === 0) {
      return { connected: false, connectionCount: 0 };
    }

    const primaryConnection = activeConnections[0];
    return {
      connected: true,
      authType: primaryConnection.authType,
      accessTier: primaryConnection.accessTier,
      connectionCount: activeConnections.length,
    };
  }

  // Private methods

  private handleMessage(messages: any[]): void {
    messages.forEach(message => {
      try {
        if (message.type === 'signal') {
          const notification: SignalNotification = message;

          // Apply preference filters
          if (this.shouldProcessNotification(notification)) {
            // Send to all handlers
            this.messageHandlers.forEach(handler => handler(notification));

            // Show browser notification if enabled
            if (this.preferences.browserPush) {
              this.showBrowserNotification(notification);
            }

            // Play sound if enabled
            if (this.preferences.sounds) {
              this.playNotificationSound();
            }
          }
        }
      } catch (error) {
        console.error('Error processing notification:', error);
      }
    });
  }

  private shouldProcessNotification(notification: SignalNotification): boolean {
    // Filter by minimum confidence
    if (notification.data.confidence_score < this.preferences.minimumConfidence) {
      return false;
    }

    // Filter by signal types
    if (
      this.preferences.signalTypes.length > 0 &&
      !this.preferences.signalTypes.includes(notification.data.signal_type)
    ) {
      return false;
    }

    return true;
  }

  private async getTokenBalance(walletAddress: string): Promise<bigint> {
    // TODO: Replace with real onchain token balance check
    // For now, simulate based on wallet address
    const simulatedBalance = walletAddress.endsWith('0')
      ? BigInt(100000)
      : walletAddress.endsWith('1')
      ? BigInt(10000)
      : walletAddress.endsWith('2')
      ? BigInt(1000)
      : BigInt(0);

    console.log(`🪙 Simulated token balance: ${simulatedBalance.toString()} $4EX`);
    return simulatedBalance;
  }

  private calculateAccessTier(tokenBalance: bigint): AccessTier {
    if (tokenBalance >= BigInt(100000)) return 'whale';
    if (tokenBalance >= BigInt(10000)) return 'holder';
    if (tokenBalance >= BigInt(1000)) return 'premium';
    return 'free';
  }

  private canAccessTier(userTier: AccessTier, requestedTier: AccessTier): boolean {
    const tierHierarchy = ['free', 'premium', 'holder', 'whale'];
    const userLevel = tierHierarchy.indexOf(userTier);
    const requestedLevel = tierHierarchy.indexOf(requestedTier);
    return userLevel >= requestedLevel;
  }

  private loadPreferences(): void {
    if (typeof window === 'undefined') {
      // Server-side rendering - use defaults
      return;
    }

    try {
      const stored = localStorage.getItem('4ex-notification-preferences');
      this.preferences = stored
        ? JSON.parse(stored)
        : {
            sounds: true,
            browserPush: false,
            signalTypes: ['BUY', 'SELL'],
            minimumConfidence: 0.7,
          };
    } catch (error) {
      console.warn('Failed to load preferences from localStorage:', error);
      // Use defaults on error
    }
  }

  private savePreferences(): void {
    if (typeof window === 'undefined') {
      // Server-side rendering - skip saving
      return;
    }

    try {
      localStorage.setItem('4ex-notification-preferences', JSON.stringify(this.preferences));
    } catch (error) {
      console.warn('Failed to save preferences to localStorage:', error);
    }
  }

  private generateAnonymousId(): string {
    return `anon_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private setupBrowserNotifications(): void {
    if (typeof window === 'undefined') {
      // Server-side rendering - skip browser notifications
      return;
    }

    if ('Notification' in window) {
      this.preferences.browserPush = Notification.permission === 'granted';
    }
  }

  private configureBrowserPush(enabled: boolean): void {
    if (typeof window === 'undefined') {
      // Server-side rendering - skip browser push config
      return;
    }

    if (enabled && 'Notification' in window && Notification.permission !== 'granted') {
      Notification.requestPermission().then(permission => {
        this.preferences.browserPush = permission === 'granted';
        this.savePreferences();
      });
    }
  }

  private showBrowserNotification(notification: SignalNotification): void {
    if (typeof window === 'undefined') {
      // Server-side rendering - skip browser notifications
      return;
    }

    if ('Notification' in window && Notification.permission === 'granted') {
      const { data } = notification;
      new Notification(`🎯 ${data.signal_type} Signal - ${data.pair}`, {
        body: `Entry: ${data.entry_price} | Confidence: ${Math.round(
          data.confidence_score * 100
        )}%`,
        icon: '/favicon.ico',
        tag: data.signal_id,
        requireInteraction: false,
      });
    }
  }

  private configureSounds(enabled: boolean): void {
    // Configure notification sounds
    this.preferences.sounds = enabled;
  }

  private playNotificationSound(): void {
    if (typeof window === 'undefined') {
      // Server-side rendering - skip sounds
      return;
    }

    // Simple notification sound
    try {
      const audio = new Audio('/notification-sound.mp3');
      audio.volume = 0.3;
      audio.play().catch(() => {
        // Ignore sound errors
      });
    } catch (error) {
      // Ignore sound errors
    }
  }
}

// Export singleton instance only on client side
export const onchainNotificationManager =
  typeof window !== 'undefined' ? OnchainNotificationManager.getInstance() : null;

'use client';

import { ConditionalMotionDiv } from '@/components/ui';
import { useOptimizedWebSocket } from '@/hooks/useOptimizedWebSocket';
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';

interface CurrencyPair {
  pair: string;
  value: string;
  increased?: boolean;
  change?: number;
  changePercent?: string;
  lastUpdate?: number;
}

const initialPairs: CurrencyPair[] = [
  { pair: 'EUR/USD', value: '1.0921' },
  { pair: 'GBP/USD', value: '1.2634' },
  { pair: 'USD/JPY', value: '107.23' },
  { pair: 'USD/CHF', value: '0.9612' },
  { pair: 'EUR/GBP', value: '0.8641' },
  { pair: 'EUR/JPY', value: '117.23' },
  { pair: 'GBP/JPY', value: '135.23' },
  { pair: 'USD/CAD', value: '1.3634' },
  { pair: 'AUD/USD', value: '0.6923' },
  { pair: 'NZD/USD', value: '0.6423' },
  { pair: 'EUR/CHF', value: '0.9723' },
  { pair: 'AUD/CAD', value: '0.9134' },
  { pair: 'GBP/CHF', value: '1.1234' },
  { pair: 'USD/SEK', value: '10.4521' },
  { pair: 'USD/NOK', value: '10.2341' },
];

interface OptimizedCurrencyTickerProps {
  /**
   * Whether to enable live price updates via WebSocket
   */
  enableLiveUpdates?: boolean;
  /**
   * Animation speed for the ticker (lower = faster)
   */
  animationDuration?: number;
  /**
   * Whether to enable hover interactions
   */
  enableHover?: boolean;
  /**
   * Throttle interval for price updates (ms)
   */
  updateThrottleMs?: number;
}

/**
 * Optimized CurrencyTicker component using Web Worker for WebSocket handling
 * Includes throttled updates, memory cleanup, and performance optimizations
 */
export const OptimizedCurrencyTicker: React.FC<OptimizedCurrencyTickerProps> = ({
  enableLiveUpdates = true,
  animationDuration = 50,
  enableHover = true,
  updateThrottleMs = 200,
}) => {
  const [prices, setPrices] = useState<CurrencyPair[]>(initialPairs);
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(0);
  const lastUpdateRef = useRef<{ [key: string]: number }>({});
  const priceHistoryRef = useRef<{ [key: string]: number[] }>({});

  // Memoized WebSocket configuration
  const webSocketConfig = useMemo(
    () => ({
      url: 'wss://ws.finnhub.io?token=cutvmf1r01qv6ijkok70cutvmf1r01qv6ijkok7g',
      throttleMs: updateThrottleMs,
      reconnectDelay: 2000,
      maxReconnectAttempts: 5,
    }),
    [updateThrottleMs]
  );

  // Optimized price update handler with memory management
  const handlePriceUpdate = useCallback(
    (trades: any[]) => {
      if (!trades || trades.length === 0) return;

      const now = Date.now();
      const updates: { [key: string]: CurrencyPair } = {};

      trades.forEach(trade => {
        if (!trade.s || !trade.p) return;

        // Convert symbol: "OANDA:EUR_USD" -> "EUR/USD"
        const pair = trade.s.includes(':')
          ? trade.s.split(':')[1].replace('_', '/')
          : trade.s.replace('_', '/');

        // Check if this pair is in our display list
        const existingPairIndex = prices.findIndex(p => p.pair === pair);
        if (existingPairIndex === -1) return;

        const existingPair = prices[existingPairIndex];
        const newValue = parseFloat(trade.p);
        const oldValue = parseFloat(existingPair.value);

        // Skip if price hasn't changed significantly (prevent unnecessary updates)
        if (Math.abs(newValue - oldValue) < 0.0001) return;

        // Update price history for trend calculation (keep last 10 values)
        if (!priceHistoryRef.current[pair]) {
          priceHistoryRef.current[pair] = [];
        }
        priceHistoryRef.current[pair].push(newValue);
        if (priceHistoryRef.current[pair].length > 10) {
          priceHistoryRef.current[pair].shift();
        }

        // Calculate change and trend
        const change = newValue - oldValue;
        const changePercent = ((change / oldValue) * 100).toFixed(2);
        const increased = change > 0;

        updates[pair] = {
          ...existingPair,
          value: newValue.toFixed(4),
          increased,
          change,
          changePercent: `${change > 0 ? '+' : ''}${changePercent}%`,
          lastUpdate: now,
        };

        lastUpdateRef.current[pair] = now;
      });

      // Batch update state if we have changes
      if (Object.keys(updates).length > 0) {
        setPrices(prevPrices => prevPrices.map(pair => updates[pair.pair] || pair));
      }
    },
    [prices]
  );

  // WebSocket connection with optimized handlers
  const { isConnected, isConnecting, error, connect, disconnect, subscribe, unsubscribe } =
    useOptimizedWebSocket({
      ...webSocketConfig,
      onMessage: handlePriceUpdate,
      onConnect: () => {
        console.log('CurrencyTicker: WebSocket connected');
      },
      onDisconnect: () => {
        console.log('CurrencyTicker: WebSocket disconnected');
      },
      onError: error => {
        console.error('CurrencyTicker WebSocket error:', error);
      },
    });

  // Subscribe to currency pairs when connected
  useEffect(() => {
    if (!enableLiveUpdates || !isConnected) return;

    const subscriptions = initialPairs.map(({ pair }) => ({
      type: 'subscribe',
      symbol: 'OANDA:' + pair.replace('/', '_'),
    }));

    subscriptions.forEach(subscription => {
      subscribe(subscription);
    });

    return () => {
      subscriptions.forEach(subscription => {
        unsubscribe({ ...subscription, type: 'unsubscribe' });
      });
    };
  }, [isConnected, enableLiveUpdates, subscribe, unsubscribe]);

  // Container width calculation with debouncing
  const updateContainerWidth = useCallback(() => {
    if (containerRef.current) {
      const width = containerRef.current.scrollWidth / 2;
      setContainerWidth(width);
    }
  }, []);

  useEffect(() => {
    updateContainerWidth();

    let timeoutId: NodeJS.Timeout;
    const debouncedResize = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(updateContainerWidth, 100);
    };

    window.addEventListener('resize', debouncedResize);
    return () => {
      clearTimeout(timeoutId);
      window.removeEventListener('resize', debouncedResize);
    };
  }, [updateContainerWidth]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Clear price history to prevent memory leaks
      priceHistoryRef.current = {};
      lastUpdateRef.current = {};

      if (isConnected) {
        disconnect();
      }
    };
  }, [isConnected, disconnect]);

  // Memoized ticker items to prevent unnecessary re-renders
  const tickerItems = useMemo(() => {
    return [...prices, ...prices].map((item, index) => {
      const isRecent = item.lastUpdate && Date.now() - item.lastUpdate < 5000;

      return (
        <div
          key={`${item.pair}-${index}`}
          className={`flex items-center space-x-2 transition-opacity duration-300 ${
            isRecent ? 'opacity-100' : 'opacity-90'
          }`}
        >
          <span className="font-bold text-white whitespace-nowrap">{item.pair}</span>
          <span
            className={`whitespace-nowrap font-mono transition-colors duration-300 ${
              item.increased === true
                ? 'text-green-400'
                : item.increased === false
                ? 'text-red-400'
                : 'text-gray-300'
            }`}
          >
            {item.value}
          </span>
          {item.changePercent && (
            <span
              className={`text-xs whitespace-nowrap ${
                item.increased === true ? 'text-green-400' : 'text-red-400'
              }`}
            >
              {item.changePercent}
            </span>
          )}
        </div>
      );
    });
  }, [prices]);

  // Connection status indicator (only show during connection issues)
  const connectionStatus = useMemo(() => {
    if (!enableLiveUpdates) return null;

    if (isConnecting) {
      return (
        <div className="absolute top-0 right-0 px-2 py-1 bg-yellow-600 text-xs text-white rounded-bl">
          Connecting...
        </div>
      );
    }

    if (error) {
      return (
        <div className="absolute top-0 right-0 px-2 py-1 bg-red-600 text-xs text-white rounded-bl">
          Connection Error
        </div>
      );
    }

    return null;
  }, [enableLiveUpdates, isConnecting, error]);

  return (
    <div className="relative w-full overflow-hidden bg-black py-2 pt-4">
      {connectionStatus}

      <div ref={containerRef} className="flex space-x-8 will-change-transform">
        <ConditionalMotionDiv
          className="flex space-x-8"
          enableMotion={true}
          motionProps={{
            animate: {
              x: [-containerWidth, 0],
            },
            transition: {
              x: {
                repeat: Infinity,
                repeatType: 'loop',
                duration: animationDuration,
                ease: 'linear',
              },
            },
          }}
          fallbackClassName="animate-scroll-ticker"
          forceGPU={true}
        >
          {tickerItems.map((item, index) => (
            <ConditionalMotionDiv
              key={index}
              className="flex-shrink-0"
              enableMotion={enableHover}
              motionProps={{
                whileHover: enableHover ? { scale: 1.05 } : {},
                transition: { duration: 0.2 },
              }}
              fallbackClassName=""
            >
              {item}
            </ConditionalMotionDiv>
          ))}
        </ConditionalMotionDiv>
      </div>
    </div>
  );
};

export default OptimizedCurrencyTicker;

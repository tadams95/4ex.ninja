'use client';

import { useTradingWebSocket } from '@/hooks/useWebSocket';
import { AnimatePresence, motion } from 'framer-motion';
import React, { memo, useEffect, useMemo, useRef } from 'react';

interface CurrencyData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  timestamp: number;
}

interface CurrencyTickerOptimizedProps {
  symbols?: string[];
  updateInterval?: number;
  showChange?: boolean;
  showPercentage?: boolean;
  maxItems?: number;
  wsUrl?: string;
  className?: string;
}

// Memoized currency item component to prevent unnecessary re-renders
const CurrencyItem = memo(
  ({
    data,
    showChange,
    showPercentage,
  }: {
    data: CurrencyData;
    showChange: boolean;
    showPercentage: boolean;
  }) => {
    const isPositive = data.change >= 0;
    const changeColor = isPositive ? 'text-green-500' : 'text-red-500';
    const bgColor = isPositive ? 'bg-green-500/10' : 'bg-red-500/10';

    return (
      <motion.div
        layout
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{
          duration: 0.3,
          layout: { duration: 0.2 },
        }}
        className={`flex items-center space-x-3 p-3 rounded-lg ${bgColor} 
                  border border-gray-200 dark:border-gray-700 
                  hover:shadow-md transition-shadow duration-200`}
      >
        <div className="flex-1">
          <div className="font-semibold text-gray-900 dark:text-gray-100">{data.symbol}</div>
          <div className="text-lg font-mono text-gray-800 dark:text-gray-200">
            ${data.price.toFixed(4)}
          </div>
        </div>

        {(showChange || showPercentage) && (
          <div className="text-right">
            {showChange && (
              <div className={`text-sm font-medium ${changeColor}`}>
                {isPositive ? '+' : ''}
                {data.change.toFixed(4)}
              </div>
            )}
            {showPercentage && (
              <div className={`text-xs ${changeColor}`}>
                ({isPositive ? '+' : ''}
                {data.changePercent.toFixed(2)}%)
              </div>
            )}
          </div>
        )}
      </motion.div>
    );
  }
);

CurrencyItem.displayName = 'CurrencyItem';

// Connection status indicator
const ConnectionStatus = memo(
  ({ isConnected, reconnectAttempts }: { isConnected: boolean; reconnectAttempts: number }) => (
    <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
      <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
      <span>
        {isConnected
          ? 'Connected'
          : `Disconnected ${reconnectAttempts > 0 ? `(${reconnectAttempts} attempts)` : ''}`}
      </span>
    </div>
  )
);

ConnectionStatus.displayName = 'ConnectionStatus';

const CurrencyTickerOptimized: React.FC<CurrencyTickerOptimizedProps> = ({
  symbols = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD'],
  showChange = true,
  showPercentage = true,
  maxItems = 5,
  wsUrl = 'wss://api.example.com/currency-feed',
  className = '',
}) => {
  const priceDataRef = useRef<Map<string, CurrencyData>>(new Map());
  const lastUpdateRef = useRef<number>(Date.now());

  // Use the trading WebSocket hook with optimized settings
  const { isConnected, reconnectAttempts, lastMessage, sendMessage } = useTradingWebSocket(
    wsUrl,
    messages => {
      // Handle batched messages from throttled updates
      const currentTime = Date.now();

      if (Array.isArray(messages)) {
        // Process the latest message from each symbol to avoid stale data
        const latestBySymbol = new Map<string, any>();

        messages.forEach(message => {
          if (message.symbol && symbols.includes(message.symbol)) {
            latestBySymbol.set(message.symbol, message);
          }
        });

        // Update price data with latest values
        latestBySymbol.forEach(message => {
          const existing = priceDataRef.current.get(message.symbol);
          const previousPrice = existing?.price || message.price;

          const currencyData: CurrencyData = {
            symbol: message.symbol,
            price: message.price,
            change: message.price - previousPrice,
            changePercent: ((message.price - previousPrice) / previousPrice) * 100,
            timestamp: currentTime,
          };

          priceDataRef.current.set(message.symbol, currencyData);
        });

        lastUpdateRef.current = currentTime;
      }
    }
  );

  // Subscribe to symbols when connection is established
  useEffect(() => {
    if (isConnected && symbols.length > 0) {
      sendMessage({
        type: 'subscribe',
        symbols: symbols,
        throttle: 50, // Request server-side throttling as well
      });
    }
  }, [isConnected, symbols, sendMessage]);

  // Memoized sorted currency data to prevent unnecessary re-renders
  const sortedCurrencyData = useMemo(() => {
    const data = Array.from(priceDataRef.current.values())
      .filter(item => symbols.includes(item.symbol))
      .sort((a, b) => symbols.indexOf(a.symbol) - symbols.indexOf(b.symbol))
      .slice(0, maxItems);

    return data;
  }, [symbols, maxItems, lastMessage]); // lastMessage as dependency to trigger updates

  // Fallback CSS animation class for when motion is disabled
  const tickerClassName = `currency-ticker-optimized ${className}`;

  return (
    <div className={`space-y-4 ${tickerClassName}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Currency Rates</h3>
        <ConnectionStatus isConnected={isConnected} reconnectAttempts={reconnectAttempts} />
      </div>

      <div className="space-y-2">
        <AnimatePresence mode="popLayout">
          {sortedCurrencyData.map(data => (
            <CurrencyItem
              key={data.symbol}
              data={data}
              showChange={showChange}
              showPercentage={showPercentage}
            />
          ))}
        </AnimatePresence>

        {sortedCurrencyData.length === 0 && (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            {isConnected ? 'Waiting for currency data...' : 'Connecting to currency feed...'}
          </div>
        )}
      </div>

      {/* Performance indicator - only show in development */}
      {process.env.NODE_ENV === 'development' && (
        <div className="text-xs text-gray-400 border-t pt-2">
          Last update: {new Date(lastUpdateRef.current).toLocaleTimeString()}
          <br />
          Items: {sortedCurrencyData.length} | Connected: {isConnected ? 'Yes' : 'No'}
        </div>
      )}
    </div>
  );
};

export default memo(CurrencyTickerOptimized);

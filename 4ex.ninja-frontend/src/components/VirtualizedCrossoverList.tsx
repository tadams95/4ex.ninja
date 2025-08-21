'use client';

import { ConditionalMotionDiv } from '@/components/ui';
import { Crossover } from '@/types';
import React, { memo, useEffect, useMemo, useRef, useState } from 'react';
import { FixedSizeList as List } from 'react-window';

interface VirtualizedCrossoverListProps {
  crossovers: Crossover[];
  height?: number;
  itemHeight?: number;
  enableVirtualization?: boolean;
  onItemClick?: (crossover: Crossover) => void;
}

interface CrossoverItemData {
  crossovers: Crossover[];
  onItemClick?: (crossover: Crossover) => void;
}

// Memoized crossover item for virtualized list
const VirtualizedCrossoverItem = memo(
  ({
    index,
    style,
    data,
  }: {
    index: number;
    style: React.CSSProperties;
    data: CrossoverItemData;
  }) => {
    const crossover = data.crossovers[index];

    // Memoize expensive calculations for each crossover
    const itemData = useMemo(
      () => ({
        borderColor: crossover.crossoverType === 'BULLISH' ? 'border-green-500' : 'border-red-500',
        badgeStyle:
          crossover.crossoverType === 'BULLISH'
            ? 'bg-green-500/20 text-green-500'
            : 'bg-red-500/20 text-red-400',
        formattedTimestamp: new Date(crossover.timestamp).toLocaleString(),
      }),
      [crossover.crossoverType, crossover.timestamp]
    );

    const handleClick = () => {
      if (data.onItemClick) {
        data.onItemClick(crossover);
      }
    };

    return (
      <div style={style} className="px-2">
        <div
          className={`bg-neutral-800 rounded-lg p-6 shadow-lg border-l-4 ${itemData.borderColor} cursor-pointer hover:bg-neutral-700 transition-colors duration-200 mb-4 border border-neutral-600`}
          onClick={handleClick}
        >
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-white">{crossover.pair}</h2>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${itemData.badgeStyle}`}>
              {crossover.crossoverType}
            </span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <p className="text-neutral-400">Timeframe:</p>
              <p className="font-medium text-white">{crossover.timeframe}</p>
            </div>
            <div className="flex justify-between">
              <p className="text-neutral-400">Price:</p>
              <p className="font-medium text-white">{crossover.price}</p>
            </div>
            {crossover.confidence && (
              <div className="flex justify-between">
                <p className="text-neutral-400">Confidence:</p>
                <p className="font-medium text-blue-400">
                  {(crossover.confidence * 100).toFixed(0)}%
                </p>
              </div>
            )}
            {crossover.strategy_type && (
              <div className="flex justify-between">
                <p className="text-neutral-400">Strategy:</p>
                <p className="font-medium text-purple-400">{crossover.strategy_type}</p>
              </div>
            )}
            {crossover.status && (
              <div className="flex justify-between">
                <p className="text-neutral-400">Status:</p>
                <p
                  className={`font-medium ${
                    crossover.status === 'ACTIVE' ? 'text-green-400' : 'text-neutral-500'
                  }`}
                >
                  {crossover.status}
                </p>
              </div>
            )}
            <p className="text-sm text-neutral-500 mt-4">{itemData.formattedTimestamp}</p>
          </div>
        </div>
      </div>
    );
  }
);

VirtualizedCrossoverItem.displayName = 'VirtualizedCrossoverItem';

// Non-virtualized fallback for smaller lists
const NonVirtualizedCrossoverItem = memo(
  ({
    crossover,
    index,
    onItemClick,
  }: {
    crossover: Crossover;
    index: number;
    onItemClick?: (crossover: Crossover) => void;
  }) => {
    const itemData = useMemo(
      () => ({
        borderColor: crossover.crossoverType === 'BULLISH' ? 'border-green-500' : 'border-red-500',
        badgeStyle:
          crossover.crossoverType === 'BULLISH'
            ? 'bg-green-500/20 text-green-500'
            : 'bg-red-500/20 text-red-400',
        formattedTimestamp: new Date(crossover.timestamp).toLocaleString(),
        staggerDelay: Math.min(index + 1, 5),
      }),
      [crossover.crossoverType, crossover.timestamp, index]
    );

    const handleClick = () => {
      if (onItemClick) {
        onItemClick(crossover);
      }
    };

    return (
      <ConditionalMotionDiv
        key={crossover._id}
        motionProps={{
          initial: { opacity: 0, y: 20 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.3, delay: index * 0.1 },
        }}
        fallbackClassName={`animate-slide-up animate-stagger-${itemData.staggerDelay}`}
        className={`bg-neutral-800 rounded-lg p-6 shadow-lg border-l-4 ${itemData.borderColor} cursor-pointer hover:bg-neutral-700 transition-colors duration-200 border border-neutral-600`}
        onClick={handleClick}
      >
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-white">{crossover.pair}</h2>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${itemData.badgeStyle}`}>
            {crossover.crossoverType}
          </span>
        </div>
        <div className="space-y-2">
          <div className="flex justify-between">
            <p className="text-neutral-400">Timeframe:</p>
            <p className="font-medium text-white">{crossover.timeframe}</p>
          </div>
          <div className="flex justify-between">
            <p className="text-neutral-400">Price:</p>
            <p className="font-medium text-white">{crossover.price}</p>
          </div>
          {crossover.confidence && (
            <div className="flex justify-between">
              <p className="text-neutral-400">Confidence:</p>
              <p className="font-medium text-blue-400">
                {(crossover.confidence * 100).toFixed(0)}%
              </p>
            </div>
          )}
          {crossover.strategy_type && (
            <div className="flex justify-between">
              <p className="text-neutral-400">Strategy:</p>
              <p className="font-medium text-purple-400">{crossover.strategy_type}</p>
            </div>
          )}
          {crossover.status && (
            <div className="flex justify-between">
              <p className="text-neutral-400">Status:</p>
              <p
                className={`font-medium ${
                  crossover.status === 'ACTIVE' ? 'text-green-400' : 'text-neutral-500'
                }`}
              >
                {crossover.status}
              </p>
            </div>
          )}
          <p className="text-sm text-neutral-500 mt-4">{itemData.formattedTimestamp}</p>
        </div>
      </ConditionalMotionDiv>
    );
  }
);

NonVirtualizedCrossoverItem.displayName = 'NonVirtualizedCrossoverItem';

/**
 * VirtualizedCrossoverList - Optimized list component for large datasets
 * Automatically switches between virtualized and non-virtualized rendering based on data size
 */
const VirtualizedCrossoverList: React.FC<VirtualizedCrossoverListProps> = memo(
  ({ crossovers, height = 600, itemHeight = 200, enableVirtualization = true, onItemClick }) => {
    const listRef = useRef<List>(null);
    const [containerHeight, setContainerHeight] = useState(height);

    // Threshold for enabling virtualization (optimize for lists larger than 50 items)
    const VIRTUALIZATION_THRESHOLD = 50;
    const shouldVirtualize = enableVirtualization && crossovers.length > VIRTUALIZATION_THRESHOLD;

    // Dynamic height calculation based on screen size
    useEffect(() => {
      const updateHeight = () => {
        const windowHeight = window.innerHeight;
        const maxHeight = Math.min(windowHeight * 0.7, height);
        setContainerHeight(maxHeight);
      };

      updateHeight();
      window.addEventListener('resize', updateHeight);
      return () => window.removeEventListener('resize', updateHeight);
    }, [height]);

    // Memoize item data to prevent unnecessary re-renders
    const itemData = useMemo(
      () => ({
        crossovers,
        onItemClick,
      }),
      [crossovers, onItemClick]
    );

    // Performance metrics for development
    const renderMetrics = useMemo(() => {
      if (process.env.NODE_ENV !== 'development') return null;

      return {
        totalItems: crossovers.length,
        isVirtualized: shouldVirtualize,
        memoryEstimate: shouldVirtualize
          ? `~${Math.ceil(containerHeight / itemHeight)} items rendered`
          : `All ${crossovers.length} items rendered`,
        performanceGain: shouldVirtualize
          ? `${Math.round(
              (1 - containerHeight / itemHeight / crossovers.length) * 100
            )}% memory reduction`
          : 'No virtualization needed',
      };
    }, [crossovers.length, shouldVirtualize, containerHeight, itemHeight]);

    if (crossovers.length === 0) {
      return (
        <div className="text-center py-8 text-neutral-500">No crossover signals available.</div>
      );
    }

    if (shouldVirtualize) {
      return (
        <div className="space-y-4">
          {/* Virtualized list for large datasets */}
          <div className="bg-neutral-800 rounded-lg overflow-hidden">
            <List
              ref={listRef}
              height={containerHeight}
              itemCount={crossovers.length}
              itemSize={itemHeight}
              itemData={itemData}
              width="100%"
              className="scrollbar-thin scrollbar-thumb-neutral-600 scrollbar-track-neutral-800"
            >
              {VirtualizedCrossoverItem}
            </List>
          </div>

          {/* Performance info in development */}
          {renderMetrics && (
            <div className="text-xs text-neutral-400 bg-neutral-800 rounded p-2 border-l-4 border-blue-500">
              <div className="font-semibold mb-1">Virtualization Performance:</div>
              <div>Total Items: {renderMetrics.totalItems}</div>
              <div>Rendered: {renderMetrics.memoryEstimate}</div>
              <div>Performance Gain: {renderMetrics.performanceGain}</div>
            </div>
          )}
        </div>
      );
    }

    // Non-virtualized list for smaller datasets
    return (
      <div className="space-y-4">
        {crossovers.map((crossover, index) => (
          <NonVirtualizedCrossoverItem
            key={crossover._id}
            crossover={crossover}
            index={index}
            onItemClick={onItemClick}
          />
        ))}

        {/* Performance info in development */}
        {renderMetrics && (
          <div className="text-xs text-neutral-400 bg-neutral-800 rounded p-2 border-l-4 border-green-500">
            <div className="font-semibold mb-1">Standard Rendering:</div>
            <div>Total Items: {renderMetrics.totalItems}</div>
            <div>Status: {renderMetrics.memoryEstimate}</div>
            <div>Note: Virtualization disabled for optimal performance with small datasets</div>
          </div>
        )}
      </div>
    );
  }
);

VirtualizedCrossoverList.displayName = 'VirtualizedCrossoverList';

export default VirtualizedCrossoverList;

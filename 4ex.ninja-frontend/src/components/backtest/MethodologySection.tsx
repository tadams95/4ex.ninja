'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { mockMethodologyData, simulateApiDelay } from './mockData';

interface MethodologyData {
  strategy_methodology: string;
  performance_attribution: string;
  last_updated: string;
}

const API_BASE = 'http://157.230.58.248:8000';

/**
 * Methodology Section Component
 *
 * Displays the comprehensive strategy methodology and implementation details
 * Organized into collapsible sections for better UX
 */
export default function MethodologySection() {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));

  const {
    data: methodology,
    isLoading,
    error,
  } = useQuery<MethodologyData>({
    queryKey: ['backtest-methodology'],
    queryFn: async () => {
      try {
        const response = await fetch(`${API_BASE}/api/v1/backtest/page/methodology`);
        if (!response.ok) {
          throw new Error(`API not available: ${response.status}`);
        }
        const result = await response.json();
        return result.data; // Extract data from the response wrapper
      } catch (error) {
        // Fallback to mock data for development
        console.log('Using mock data for methodology (API not available)');
        await simulateApiDelay();
        return mockMethodologyData;
      }
    },
    staleTime: 10 * 60 * 1000, // 10 minutes - methodology doesn't change often
  });

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const expandAll = () => {
    setExpandedSections(new Set(['strategy_methodology', 'performance_attribution']));
  };

  const collapseAll = () => {
    setExpandedSections(new Set());
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse">
          <div className="h-6 bg-neutral-700 rounded mb-4 w-48"></div>
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
              <div className="h-5 bg-neutral-700 rounded mb-3 w-64"></div>
              <div className="space-y-2">
                <div className="h-4 bg-neutral-700 rounded w-full"></div>
                <div className="h-4 bg-neutral-700 rounded w-5/6"></div>
                <div className="h-4 bg-neutral-700 rounded w-4/6"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-red-400 mb-4">Strategy Methodology</h3>
        <p className="text-neutral-400 text-sm">Error loading methodology: {error.message}</p>
      </div>
    );
  }

  if (!methodology) {
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-neutral-300 mb-4">Strategy Methodology</h3>
        <p className="text-neutral-400 text-sm">No methodology documentation available</p>
      </div>
    );
  }

  // Create sections from the API data
  const sections = [
    {
      key: 'strategy_methodology',
      title: 'Strategy Methodology',
      content: methodology.strategy_methodology || 'No strategy methodology available',
      hasContent: Boolean(
        methodology.strategy_methodology && methodology.strategy_methodology.trim()
      ),
    },
    {
      key: 'performance_attribution',
      title: 'Performance Attribution',
      content: methodology.performance_attribution || 'No performance attribution available',
      hasContent: Boolean(
        methodology.performance_attribution && methodology.performance_attribution.trim()
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-white">Strategy Methodology</h2>
        <div className="flex space-x-2">
          <button
            onClick={expandAll}
            className="px-3 py-1 text-sm bg-neutral-700 text-neutral-300 rounded-md hover:bg-neutral-600 transition-colors"
          >
            Expand All
          </button>
          <button
            onClick={collapseAll}
            className="px-3 py-1 text-sm bg-neutral-700 text-neutral-300 rounded-md hover:bg-neutral-600 transition-colors"
          >
            Collapse All
          </button>
        </div>
      </div>

      {/* Methodology Sections */}
      <div className="space-y-4">
        {sections.map(section => {
          const isExpanded = expandedSections.has(section.key);

          return (
            <div key={section.key} className="bg-neutral-800 border border-neutral-700 rounded-lg">
              {/* Section Header */}
              <button
                onClick={() => toggleSection(section.key)}
                className="w-full px-6 py-4 flex justify-between items-center text-left hover:bg-neutral-750 transition-colors"
              >
                <h3 className="text-lg font-semibold text-white">{section.title}</h3>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-neutral-400">
                    {section.hasContent ? 'Available' : 'No data'}
                  </span>
                  <svg
                    className={`w-5 h-5 text-neutral-400 transition-transform ${
                      isExpanded ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </div>
              </button>

              {/* Section Content */}
              {isExpanded && (
                <div className="px-6 pb-6">
                  <div className="border-l-2 border-blue-500 pl-4">
                    <div className="text-sm text-neutral-300 leading-relaxed">
                      {section.hasContent ? (
                        section.content.split('\n').map((paragraph, pIndex) => (
                          <p key={pIndex} className="mb-2 last:mb-0">
                            {paragraph}
                          </p>
                        ))
                      ) : (
                        <p className="text-neutral-400 italic">{section.content}</p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Summary Footer */}
      <div className="bg-neutral-900 border border-neutral-600 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-3">Documentation Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-neutral-400">Total Sections:</span>
            <span className="text-white ml-2">{sections.length}</span>
          </div>
          <div>
            <span className="text-neutral-400">Sections with Data:</span>
            <span className="text-white ml-2">{sections.filter(s => s.hasContent).length}</span>
          </div>
          <div>
            <span className="text-neutral-400">Expanded:</span>
            <span className="text-white ml-2">{expandedSections.size}</span>
          </div>
          {methodology.last_updated && (
            <div className="md:col-span-3 mt-2 pt-2 border-t border-neutral-700">
              <span className="text-neutral-400">Last Updated:</span>
              <span className="text-white ml-2">
                {new Date(methodology.last_updated).toLocaleDateString()}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

'use client';

import { useState } from 'react';

/**
 * Methodology Section Component
 *
 * Displays the comprehensive strategy methodology and implementation details
 * Organized into collapsible sections for better UX
 */
export default function MethodologySection() {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));

  // VERIFIED methodology based on comprehensive August 2025 optimization results
  const methodology = {
    strategy_methodology: `# Enhanced Daily EMA Strategy - Comprehensive 10-Pair Optimization Results

## Strategy Overview
The Enhanced Daily EMA Strategy employs a dual exponential moving average (EMA) crossover system optimized across 10 major forex pairs through comprehensive backtesting. Enhanced with session filtering, confluence detection, and dynamic position sizing, our August 2025 optimization revealed a realistic 50% success rate, with significant JPY pair outperformance.

### Core Strategy Components
• **Signal Generation**: EMA crossover system on daily timeframe with pair-specific optimized parameters
• **Enhancement Layer**: Session-based filtering, support/resistance confluence, dynamic position sizing
• **Risk Management**: Fixed 1.5% stop loss, 3.0% take profit (2:1 reward-to-risk ratio)
• **Position Sizing**: Risk-based sizing with signal strength and volatility adjustments
• **Trading Costs**: Realistic spread modeling (20-40 pips) with cost-adjusted performance metrics

### Strategy Enhancements
• **Session Filtering**: JPY pairs prioritized during Asian trading sessions for optimal liquidity
• **Confluence Detection**: Support/resistance level alignment for improved entry timing
• **Dynamic Sizing**: Position size adjustments based on signal strength and market volatility
• **Multi-Pair Optimization**: Pair-specific EMA parameters (20/60 vs 30/60) for maximum effectiveness

### Optimization Results Summary
**Total Pairs Tested**: 10 major forex pairs
**Profitable Pairs**: 5 (50% success rate)
**Unprofitable Pairs**: 5 (significant negative returns after costs)
**Top Performer**: USD_JPY (14.0% annual return, 70% win rate)
**Key Discovery**: JPY pairs demonstrate superior trend-following characteristics

### Profitable Pair Performance
1. **USD_JPY**: 14.0% return, 70% win rate, EMA 20/60 configuration
2. **EUR_JPY**: 13.5% return, 70% win rate, EMA 30/60 configuration  
3. **AUD_JPY**: 3.8% return, 46.7% win rate, EMA 20/60 configuration
4. **GBP_JPY**: 2.2% return, 45.5% win rate, EMA 30/60 configuration
5. **AUD_USD**: 1.5% return, 41.7% win rate, EMA 20/60 configuration

### Unprofitable Pair Results
• **EUR_USD**: -4.6% return (most surprising given high liquidity)
• **EUR_GBP**: -4.2% return (cross-pair volatility issues)
• **USD_CHF**: -3.6% return (poor trend characteristics)
• **GBP_USD**: -3.0% return (excessive volatility relative to trends)
• **USD_CAD**: -1.5% return (commodity currency challenges)`,

    performance_attribution: `# Performance Analysis & Market Insights

## Key Performance Insights

### JPY Pair Dominance Discovery
**Major Finding**: 4 out of 5 profitable pairs involve JPY, indicating strong trend-following characteristics in Japanese Yen crosses during the optimization period.

**JPY Performance Breakdown**:
- USD_JPY: 14.0% annual return (Tier 1: Highly Profitable)
- EUR_JPY: 13.5% annual return (Tier 1: Highly Profitable)
- AUD_JPY: 3.8% annual return (Tier 2: Profitable)
- GBP_JPY: 2.2% annual return (Tier 2: Profitable)

### Major Pair Underperformance
Contrary to conventional wisdom, traditionally high-liquidity major pairs showed poor performance:
- EUR_USD (-4.6%): Despite being the world's most traded pair
- GBP_USD (-3.0%): High volatility without corresponding trend strength
- Cross pairs like EUR_GBP (-4.2%) struggled significantly

### Optimal EMA Configuration Analysis
**EMA 20/60**: Effective for USD_JPY, AUD_JPY, AUD_USD
**EMA 30/60**: Optimal for EUR_JPY, GBP_JPY
**Faster EMAs (15)**: Less effective across most pairs
**Slower EMAs (45+)**: Insufficient signal generation

### Trading Cost Impact Assessment
- **High Performers**: Overcome trading costs effectively (USD_JPY, EUR_JPY)
- **Marginal Strategies**: Trading costs significantly reduce profitability
- **Cost Range**: 1.6-5.2% annual performance drag depending on pair and frequency
- **Spread Sensitivity**: Lower-return strategies become unprofitable after realistic cost modeling

## Risk-Adjusted Performance Metrics
**Win Rate Range**: 41.7% - 70.0% (profitable pairs only)
**Average Annual Return**: 6.8% across profitable pairs
**Risk Management**: Consistent 1.5% SL, 3.0% TP across all strategies
**Trade Frequency**: 10-15 trades per year per pair (quality over quantity approach)

## Market Regime Considerations
The optimization period captured specific market conditions favoring JPY trend-following. Performance may vary under different market regimes, particularly during:
- Central bank intervention periods
- High-volatility news events
- Significant shifts in global risk sentiment`,

    last_updated: '2025-08-20',
  };

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
    setExpandedSections(
      new Set(['strategy_methodology', 'performance_attribution', 'implementation_guidelines'])
    );
  };

  const collapseAll = () => {
    setExpandedSections(new Set());
  };

  // Create sections from the methodology data
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
    {
      key: 'implementation_guidelines',
      title: 'Implementation Guidelines & Risk Management',
      content: `# Implementation Guidelines Based on Optimization Results

## Recommended Portfolio Allocation
Based on verified August 2025 optimization results showing 50% success rate across 10 pairs tested:

### Tier 1: High Allocation (60% of capital)
- **USD_JPY**: 35% allocation (14.0% return, 70% win rate, 10 trades/year)
- **EUR_JPY**: 25% allocation (13.5% return, 70% win rate, 10 trades/year)

### Tier 2: Medium Allocation (30% of capital)  
- **AUD_JPY**: 15% allocation (3.8% return, 46.7% win rate, 15 trades/year)
- **GBP_JPY**: 10% allocation (2.2% return, 45.5% win rate, 11 trades/year)
- **AUD_USD**: 5% allocation (1.5% return, 41.7% win rate, 12 trades/year)

### Risk Reserve (10% of capital)
- Cash buffer for drawdown management and opportunity deployment

## Risk Management Framework

### Position Sizing
- **Maximum Risk per Trade**: 1.0% of portfolio
- **Stop Loss**: Fixed 1.5% (tested and optimized)
- **Take Profit**: Fixed 3.0% (2:1 reward-to-risk ratio)
- **Maximum Portfolio Heat**: 5% (max 5 simultaneous positions)

### Trading Cost Considerations
- **Spread Impact**: 1.6% - 5.2% annual performance drag depending on pair
- **High-Frequency Warning**: Lower-return strategies become unprofitable after costs
- **Execution Timing**: Focus on major session overlaps for better spreads

### Performance Expectations
- **Realistic Annual Returns**: 1.5% - 14.0% depending on pair allocation
- **Portfolio Blended Return**: 6-9% annually with conservative allocation
- **Win Rate Range**: 41.7% - 70% (JPY pairs consistently higher)
- **Maximum Expected Drawdown**: 8-12% during adverse market conditions

## Market Regime Considerations

### JPY-Favorable Conditions
- Strong trending markets
- Risk-on/risk-off regime clarity  
- Low intervention periods from Bank of Japan

### Risk Scenarios to Monitor
- **BoJ Intervention**: Potential JPY pair disruption
- **Major Pair Reversals**: EUR_USD, GBP_USD showed -4.6% and -3.0% returns
- **Cross-Pair Volatility**: EUR_GBP struggled with -4.2% return
- **Commodity Currency Weakness**: USD_CAD showed -1.5% return

## Implementation Phases

### Phase 1: Conservative Start (Months 1-3)
- Deploy only USD_JPY and EUR_JPY (proven 70% win rates)
- Monitor performance vs backtest expectations
- Validate cost assumptions in live environment

### Phase 2: Graduated Expansion (Months 4-6)
- Add AUD_JPY and GBP_JPY if Phase 1 performs as expected
- Maintain strict risk limits and performance tracking

### Phase 3: Full Portfolio (Months 7+)
- Consider AUD_USD addition for non-JPY diversification
- Regular performance review and parameter adjustment

## Warning: Avoided Pairs
Based on optimization results, these pairs showed consistent unprofitability:
- **EUR_USD**: -4.6% return despite high liquidity
- **GBP_USD**: -3.0% return, excessive volatility
- **USD_CHF**: -3.6% return, poor trend characteristics  
- **USD_CAD**: -1.5% return, commodity currency challenges
- **EUR_GBP**: -4.2% return, cross-pair complexity

## Performance Monitoring
- **Weekly Reviews**: JPY pair correlation and performance tracking
- **Monthly Assessments**: Portfolio rebalancing based on pair performance
- **Quarterly Optimization**: Parameter review and potential strategy updates
- **Annual Review**: Comprehensive strategy evaluation and optimization cycle`,
      hasContent: true,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-white">Enhanced Daily EMA Strategy Methodology</h2>
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
                    <div className="text-sm text-neutral-300 leading-relaxed space-y-3">
                      {section.hasContent ? (
                        section.content.split('\n').map((line, pIndex) => {
                          // Helper function to parse inline bold text
                          const parseInlineBold = (text: string) => {
                            const parts = text.split(/(\*\*[^*]+\*\*)/);
                            return parts.map((part, index) => {
                              if (part.startsWith('**') && part.endsWith('**')) {
                                return (
                                  <strong key={index} className="font-semibold text-yellow-400">
                                    {part.replace(/\*\*/g, '')}
                                  </strong>
                                );
                              }
                              return part;
                            });
                          };

                          // Handle different markdown-style elements
                          if (line.startsWith('# ')) {
                            return (
                              <h2 key={pIndex} className="text-xl font-bold text-white mt-6 mb-3">
                                {line.replace('# ', '')}
                              </h2>
                            );
                          }
                          if (line.startsWith('## ')) {
                            return (
                              <h3
                                key={pIndex}
                                className="text-lg font-semibold text-blue-400 mt-4 mb-2"
                              >
                                {line.replace('## ', '')}
                              </h3>
                            );
                          }
                          if (line.startsWith('### ')) {
                            return (
                              <h4
                                key={pIndex}
                                className="text-base font-medium text-green-400 mt-3 mb-2"
                              >
                                {line.replace('### ', '')}
                              </h4>
                            );
                          }
                          if (
                            line.startsWith('**') &&
                            line.endsWith('**') &&
                            !line.includes(': ')
                          ) {
                            return (
                              <p key={pIndex} className="font-semibold text-yellow-400 mb-1">
                                {line.replace(/\*\*/g, '')}
                              </p>
                            );
                          }
                          if (line.startsWith('- ') || line.startsWith('• ')) {
                            const content = line.replace(/^[-•] /, '');
                            return (
                              <p key={pIndex} className="ml-4 mb-1 text-neutral-300">
                                <span className="text-blue-400 mr-2">•</span>
                                {parseInlineBold(content)}
                              </p>
                            );
                          }
                          if (line.trim() === '') {
                            return <div key={pIndex} className="h-2" />;
                          }
                          return (
                            <p key={pIndex} className="mb-2 text-neutral-300">
                              {parseInlineBold(line)}
                            </p>
                          );
                        })
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
        <h3 className="text-lg font-semibold text-white mb-3">
          Enhanced Daily EMA Strategy Documentation
        </h3>
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

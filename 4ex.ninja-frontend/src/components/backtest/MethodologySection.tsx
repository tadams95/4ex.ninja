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

  // Comprehensive methodology based on actual implementation and results
  const methodology = {
    strategy_methodology: `# MA Unified Strategy - Moving Average Crossover System

## Core Strategy Logic
The MA Unified Strategy employs a sophisticated moving average crossover system designed for consistent trend-following performance across major forex pairs. The strategy operates on the principle that price trends, once established, tend to persist long enough to generate profitable trading opportunities.

### Technical Foundation
• **Primary Signal Generation**: Dual moving average crossover system with fast MA (10-50 periods) crossing above/below slow MA (50-200 periods)
• **Risk Management**: ATR-based position sizing with dynamic stop losses and take profits
• **Market Filtering**: Multi-criteria validation ensuring risk-reward ratios exceed 1.5:1
• **Timeframe Optimization**: Weekly timeframes dominate top performers (80% of strategies) due to superior noise filtering

### Strategy Variants
**Conservative Profile**: Lower volatility tolerance with tighter risk controls
- Typical Parameters: 20/50 MA crossover, 2.0x ATR stop loss, 3.0x ATR take profit
- Target Audience: Risk-averse traders seeking steady growth
- Expected Performance: 15-17% annual returns, 4-6% maximum drawdown

**Moderate Profile**: Balanced approach between risk and reward
- Typical Parameters: 15/40 MA crossover, 2.5x ATR stop loss, 3.5x ATR take profit  
- Target Audience: Balanced risk tolerance seeking higher returns
- Expected Performance: 18-24% annual returns, 7-10% maximum drawdown

### Currency Pair Selection
Priority allocation based on 5-year comprehensive backtesting:
1. **USD_CAD**: Highest robustness score (84.4%) - Primary allocation
2. **AUD_USD**: Strong consistency (83.7%) - Core position
3. **USD_CHF**: Excellent stability (83.1%) - Diversification
4. **EUR_USD**: Reliable performance (81.8%) - Secondary allocation
5. **USD_JPY & GBP_USD**: Complementary positions for portfolio balance`,

    performance_attribution: `# Performance Attribution & Validation Results

## Comprehensive 5-Year Backtest Analysis
**Testing Period**: January 2020 - December 2024 (5 complete years)
**Data Quality**: High-frequency OHLC data across 16 major forex pairs
**Total Strategies Tested**: 276 parameter combinations
**Validation Method**: Walk-forward analysis with out-of-sample testing

## Top Performance Metrics
**Best Strategy**: EUR_USD Conservative Weekly
- Annual Return: 15.6%
- Sharpe Ratio: 2.08 (exceptional risk-adjusted performance)
- Maximum Drawdown: 4.8% (excellent risk control)
- Win Rate: 59.0% (above-average success rate)

**Portfolio Leaders** (Ready for immediate deployment):
1. **USD_CAD Moderate Weekly**: 84.4% robustness, 23.5% annual return
2. **AUD_USD Conservative Weekly**: 83.7% robustness, 13.6% annual return  
3. **USD_CHF Conservative Weekly**: 83.1% robustness, 15.6% annual return

## Risk Analysis & Market Stress Testing
**Maximum Portfolio Drawdown**: 6.2% (GBP_USD Moderate)
**Average Win Rate**: 54.5% across all currency pairs
**Risk-Reward Consistency**: All strategies maintain >1.5:1 reward-to-risk ratios
**Market Regime Performance**: Validated across trending, ranging, and volatile market conditions

## Walk-Forward Validation Results
**Methodology**: 20 rolling windows of 6-month training, 3-month out-of-sample testing
**Performance Degradation**: Average 16.3% (excellent - indicates minimal overfitting)
**Consistency Score**: Average 82.4% (high stability across different market periods)
**Parameter Stability**: 72.1% (robust parameter sets that work across various conditions)

## Statistical Significance
**Confidence Level**: 95% statistical confidence in results
**Sample Size**: 5 years of continuous data (1,825 trading days)
**Transaction Costs**: Included realistic spread and slippage modeling
**Market Impact**: Tested with position sizes appropriate for retail and institutional trading

## Implementation Validation
**Live Trading Preparation**: Top 3 strategies cleared for immediate paper trading
**Monitoring Systems**: Real-time parameter drift detection implemented
**Emergency Protocols**: Automated risk management during high-impact news events
**Infrastructure**: Redis-optimized signal generation achieving <500ms execution times`,

    last_updated: '2025-08-19',
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
      title: 'Implementation Guidelines',
      content: `# Implementation Guidelines & Trading Framework

## Recommended Portfolio Allocation
**Core Allocation (60% of trading capital)**:
- USD_CAD Moderate Conservative Weekly: 25% (highest robustness)
- AUD_USD Conservative Conservative Weekly: 20% (excellent consistency)  
- USD_CHF Conservative Conservative Weekly: 15% (superior stability)

**Diversification Allocation (35% of trading capital)**:
- EUR_USD Conservative Conservative Daily: 15% (proven reliability)
- USD_JPY Conservative Conservative Weekly: 10% (portfolio balance)
- GBP_USD Conservative Conservative Weekly: 10% (complementary exposure)

**Risk Management Reserve**: 5% (emergency protocols and drawdown protection)

## Risk Management Framework
**Position Sizing**: Maximum 2% risk per trade using ATR-based calculations
**Portfolio Heat**: Maximum 6% total portfolio risk across all open positions
**Maximum Drawdown Limit**: 10% portfolio drawdown triggers emergency protocols
**Correlation Management**: Maximum 3 correlated positions (EUR/GBP/CHF group)

## Trading Schedule & Execution
**Optimal Trading Sessions**:
- London Session: 08:00-17:00 GMT (highest liquidity for EUR/GBP pairs)
- New York Session: 13:00-22:00 GMT (optimal for USD pairs)
- Avoid Asian Session: 22:00-08:00 GMT (lower liquidity, wider spreads)

**Signal Processing**:
- Weekly signals: Process on Sunday 17:00 GMT market open
- Daily signals: Process during London session for optimal execution
- Emergency protocols: Automatic position reduction during major news events

## Technology Requirements
**Infrastructure**: Redis-optimized signal generation (<500ms execution)
**Data Quality**: High-frequency OHLC data with spread modeling
**Monitoring**: Real-time parameter drift detection and performance tracking
**Backup Systems**: Redundant signal delivery through multiple channels

## Expected Performance Characteristics
**Annual Returns**: 15-25% depending on risk profile selection
**Maximum Drawdown**: 4-8% based on conservative to moderate allocation
**Win Rate**: 54-59% across different market conditions
**Sharpe Ratio**: 1.8-2.1 (excellent risk-adjusted returns)
**Trading Frequency**: 25-50 trades per year per strategy (quality over quantity)

## Monitoring & Adjustment Guidelines
**Monthly Reviews**: Performance attribution and parameter stability analysis
**Quarterly Assessments**: Walk-forward validation and strategy rebalancing
**Annual Evaluations**: Comprehensive strategy review and allocation updates
**Stress Testing**: Continuous monitoring during volatile market periods

## Emergency Protocols
**High Volatility Events**: Automatic position size reduction during major news
**Technical Failures**: Redundant signal delivery and manual override capabilities
**Market Stress**: Enhanced monitoring and potential strategy suspension
**Performance Degradation**: Automatic alerts when performance falls below expectations`,
      hasContent: true,
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

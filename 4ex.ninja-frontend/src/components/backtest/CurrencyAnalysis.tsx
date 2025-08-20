'use client';

import { useState } from 'react';

/**
 * Currency Analysis Component
 *
 * Provides detailed analysis and insights for individual currency pairs
 * Focused on trading characteristics, optimal strategies, and risk management
 */
export default function CurrencyAnalysis() {
  const [selectedCurrency, setSelectedCurrency] = useState<string>('USD_CAD');

  const currencyData = {
    USD_CAD: {
      name: 'USD/CAD',
      nickname: 'Loonie',
      robustnessScore: 84.4,
      allocation: 'Primary',
      strategy: 'Moderate MA Weekly',
      strategyDetails: 'Moderate risk MA crossover with weekly analysis',
      annualReturn: '23.5%',
      maxDrawdown: '5.2%',
      sharpeRatio: 2.1,
      winRate: '61%',
      signalReliability: '89%',
      riskProfile: 'Low-Moderate',
      marketCharacteristics: 'Known for its stability and correlation with oil prices',
      tradingSessions: 'Peak performance during London-NY overlap (12:00-17:00 GMT)',
      volatilityPatterns:
        'Lower volatility compared to EUR/GBP pairs, ideal for conservative strategies',
      economicDrivers: 'Bank of Canada policy, oil prices, US economic data',
      seasonalTrends: 'Stronger performance in Q2-Q3 due to commodity cycles',
      insights: [
        'Most stable major pair with excellent risk-adjusted returns',
        'Strong correlation with WTI crude oil prices (0.76)',
        'Responds well to Canadian employment data releases',
        'Ideal for risk-averse traders seeking consistent performance',
      ],
      strategyParams: {
        stopLoss: '2.0x ATR',
        takeProfit: '3.0x ATR',
        signalFreq: '1 per week',
        riskReward: '1.5:1 minimum',
      },
    },
    AUD_USD: {
      name: 'AUD/USD',
      nickname: 'Aussie',
      robustnessScore: 83.7,
      allocation: 'Core Position',
      strategy: 'Conservative MA Weekly',
      strategyDetails: 'Conservative risk MA crossover with weekly analysis',
      annualReturn: '16.4%',
      maxDrawdown: '5.7%',
      sharpeRatio: 1.88,
      winRate: '59%',
      signalReliability: '85%',
      riskProfile: 'Low',
      marketCharacteristics: 'Commodity currency with strong correlation to Asian markets',
      tradingSessions: 'Best during Asian-London overlap (06:00-10:00 GMT)',
      volatilityPatterns: 'Higher volatility than USD/CAD, requires wider stops',
      economicDrivers: 'RBA policy, Chinese economic data, commodity prices',
      seasonalTrends: 'Outperforms in Q4-Q1 due to Chinese New Year flows',
      insights: [
        'Strong correlation with gold and iron ore prices',
        'Highly sensitive to Chinese economic indicators',
        'Benefits from risk-on market sentiment',
        'Excellent for diversification from USD-centric pairs',
      ],
      strategyParams: {
        stopLoss: '1.5x ATR',
        takeProfit: '2.25x ATR',
        signalFreq: '1 per week',
        riskReward: '1.5:1 minimum',
      },
    },
    USD_CHF: {
      name: 'USD/CHF',
      nickname: 'Swissie',
      robustnessScore: 83.1,
      allocation: 'Diversification',
      strategy: 'Conservative MA Weekly',
      strategyDetails: 'Conservative risk MA crossover with weekly analysis',
      annualReturn: '15.6%',
      maxDrawdown: '4.8%',
      sharpeRatio: 2.2,
      winRate: '62%',
      signalReliability: '92%',
      riskProfile: 'Low',
      marketCharacteristics: 'Safe-haven currency with inverse correlation to EUR',
      tradingSessions: 'European session optimal (08:00-16:00 GMT)',
      volatilityPatterns: 'Lowest volatility among major pairs, excellent for risk-averse traders',
      economicDrivers: 'SNB intervention, European economic health, safe-haven flows',
      seasonalTrends: 'Stronger during geopolitical uncertainty periods',
      insights: [
        'Highest signal reliability at 92%',
        'Natural hedge against EUR exposure',
        'Strong safe-haven characteristics during market stress',
        'SNB intervention risk at extreme levels',
      ],
      strategyParams: {
        stopLoss: '1.5x ATR',
        takeProfit: '2.25x ATR',
        signalFreq: '1 per week',
        riskReward: '1.5:1 minimum',
      },
    },
    EUR_USD: {
      name: 'EUR/USD',
      nickname: 'Fiber',
      robustnessScore: 81.8,
      allocation: 'Secondary',
      strategy: 'Conservative MA Daily',
      strategyDetails: 'Conservative risk MA crossover with daily analysis',
      annualReturn: '18.4%',
      maxDrawdown: '6.0%',
      sharpeRatio: 1.67,
      winRate: '59%',
      signalReliability: '87%',
      riskProfile: 'Low',
      marketCharacteristics: 'Most liquid forex pair with tight spreads',
      tradingSessions: 'London session dominance (08:00-17:00 GMT)',
      volatilityPatterns: 'Moderate volatility with predictable intraday ranges',
      economicDrivers: 'ECB policy, US Federal Reserve, economic data releases',
      seasonalTrends: 'Consistent performance across all quarters',
      insights: [
        'Highest liquidity provides excellent execution',
        'Responsive to central bank policy divergence',
        'Works well with daily trading strategies',
        'Strong technical pattern recognition',
      ],
      strategyParams: {
        stopLoss: '1.5x ATR',
        takeProfit: '2.25x ATR',
        signalFreq: '5-7 per week',
        riskReward: '1.5:1 minimum',
      },
    },
    USD_JPY: {
      name: 'USD/JPY',
      nickname: 'Gopher',
      robustnessScore: 79.2,
      allocation: 'Portfolio Balance',
      strategy: 'Moderate MA Weekly',
      strategyDetails: 'Moderate risk MA crossover with weekly analysis',
      annualReturn: '21.1%',
      maxDrawdown: '8.2%',
      sharpeRatio: 1.76,
      winRate: '53%',
      signalReliability: '82%',
      riskProfile: 'Moderate',
      marketCharacteristics: 'Carry trade favorite with strong central bank influence',
      tradingSessions: 'Asian session strength (22:00-08:00 GMT)',
      volatilityPatterns: 'Trending behavior with occasional sharp reversals',
      economicDrivers: 'BoJ intervention, US-Japan yield differentials, risk sentiment',
      seasonalTrends: 'Stronger in risk-on environments, weaker during market stress',
      insights: [
        'Strong trending characteristics during clear moves',
        'Sensitive to US-Japan yield differentials',
        'BoJ intervention risk at extreme levels',
        'Excellent carry trade opportunities',
      ],
      strategyParams: {
        stopLoss: '2.0x ATR',
        takeProfit: '3.0x ATR',
        signalFreq: '1 per week',
        riskReward: '1.5:1 minimum',
      },
    },
    GBP_USD: {
      name: 'GBP/USD',
      nickname: 'Cable',
      robustnessScore: 77.8,
      allocation: 'Complementary',
      strategy: 'Conservative MA Weekly',
      strategyDetails: 'Conservative risk MA crossover with weekly analysis',
      annualReturn: '17.2%',
      maxDrawdown: '6.2%',
      sharpeRatio: 1.98,
      winRate: '59%',
      signalReliability: '78%',
      riskProfile: 'Moderate',
      marketCharacteristics: 'High volatility with strong intraday ranges',
      tradingSessions: 'London session dominance with NY extension',
      volatilityPatterns: 'Higher volatility among major pairs, requires careful risk management',
      economicDrivers: 'BoE policy, Brexit-related flows, UK economic data',
      seasonalTrends: 'Volatile performance with quarterly variations',
      insights: [
        'Strong returns with good risk management',
        'Requires experienced risk management',
        'Strong reaction to UK political developments',
        'Good for traders comfortable with moderate risk',
      ],
      strategyParams: {
        stopLoss: '1.5x ATR',
        takeProfit: '2.25x ATR',
        signalFreq: '1 per week',
        riskReward: '1.5:1 minimum',
      },
    },
  };

  const currencies = Object.keys(currencyData);
  const selectedData = currencyData[selectedCurrency as keyof typeof currencyData];

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'Low':
        return 'text-green-400';
      case 'Moderate':
        return 'text-yellow-400';
      case 'Moderate-High':
        return 'text-orange-400';
      case 'High':
        return 'text-red-400';
      default:
        return 'text-neutral-400';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 83) return 'text-green-400';
    if (score >= 80) return 'text-yellow-400';
    if (score >= 75) return 'text-orange-400';
    return 'text-red-400';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-white">Currency Analysis</h2>
          <p className="text-sm text-neutral-400">
            Detailed insights for individual currency pairs and their trading characteristics
          </p>
        </div>

        {/* Currency Selector */}
        <div className="flex flex-wrap gap-2">
          {currencies.map(currency => {
            const data = currencyData[currency as keyof typeof currencyData];
            return (
              <button
                key={currency}
                onClick={() => setSelectedCurrency(currency)}
                className={`px-3 py-2 text-sm rounded-md transition-colors ${
                  selectedCurrency === currency
                    ? 'bg-blue-600 text-white'
                    : 'bg-neutral-700 text-neutral-300 hover:bg-neutral-600'
                }`}
              >
                {data.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* Selected Currency Overview */}
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Left Column - Basic Info */}
          <div className="lg:w-1/3">
            <div className="flex items-center gap-3 mb-4">
              <h3 className="text-2xl font-bold text-white">{selectedData.name}</h3>
              <span className="text-sm text-neutral-400">({selectedData.nickname})</span>
            </div>

            <div className="space-y-3">
              <div className="grid grid-cols-[1fr,auto] gap-4 items-center">
                <span className="text-neutral-400">Robustness Score:</span>
                <span className={`font-bold ${getScoreColor(selectedData.robustnessScore)}`}>
                  {selectedData.robustnessScore}%
                </span>
              </div>
              <div className="grid grid-cols-[1fr,auto] gap-4 items-center">
                <span className="text-neutral-400">Allocation Type:</span>
                <span className="text-blue-400 font-medium">{selectedData.allocation}</span>
              </div>
              <div className="grid grid-cols-[1fr,auto] gap-4 items-center">
                <span className="text-neutral-400">Risk Profile:</span>
                <span className={`font-medium ${getRiskColor(selectedData.riskProfile)}`}>
                  {selectedData.riskProfile}
                </span>
              </div>
              <div className="grid grid-cols-[1fr,auto] gap-4 items-center">
                <span className="text-neutral-400">Optimal Strategy:</span>
                <span className="text-purple-400 font-medium text-sm text-right">
                  {selectedData.strategy}
                </span>
              </div>
            </div>
          </div>

          {/* Middle Column - Performance Metrics */}
          <div className="lg:w-1/3">
            <h4 className="text-lg font-semibold text-white mb-4">Performance Metrics</h4>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-neutral-400">Annual Return:</span>
                <span className="text-green-400 font-bold">{selectedData.annualReturn}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-400">Max Drawdown:</span>
                <span className="text-red-400 font-bold">{selectedData.maxDrawdown}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-400">Sharpe Ratio:</span>
                <span className="text-blue-400 font-bold">{selectedData.sharpeRatio}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-400">Win Rate:</span>
                <span className="text-purple-400 font-bold">{selectedData.winRate}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-400">Signal Reliability:</span>
                <span className="text-cyan-400 font-bold">{selectedData.signalReliability}</span>
              </div>
            </div>
          </div>

          {/* Right Column - Quick Insights */}
          <div className="lg:w-1/3">
            <h4 className="text-lg font-semibold text-white mb-4">Key Insights</h4>
            <div className="space-y-2">
              {selectedData.insights.map((insight, index) => (
                <div key={index} className="flex items-start gap-2">
                  <span className="text-blue-400 flex-shrink-0">•</span>
                  <span className="text-neutral-300 text-sm leading-relaxed">{insight}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Analysis Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Market Characteristics */}
        <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
          <h4 className="text-lg font-semibold text-white mb-4">Market Characteristics</h4>
          <div className="space-y-4">
            <div>
              <h5 className="text-sm font-medium text-blue-400 mb-2">Overview</h5>
              <p className="text-neutral-300 text-sm">{selectedData.marketCharacteristics}</p>
            </div>
            <div>
              <h5 className="text-sm font-medium text-green-400 mb-2">Optimal Trading Sessions</h5>
              <p className="text-neutral-300 text-sm">{selectedData.tradingSessions}</p>
            </div>
            <div>
              <h5 className="text-sm font-medium text-yellow-400 mb-2">Volatility Patterns</h5>
              <p className="text-neutral-300 text-sm">{selectedData.volatilityPatterns}</p>
            </div>
          </div>
        </div>

        {/* Economic Analysis */}
        <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
          <h4 className="text-lg font-semibold text-white mb-4">Economic Analysis</h4>
          <div className="space-y-4">
            <div>
              <h5 className="text-sm font-medium text-purple-400 mb-2">Primary Drivers</h5>
              <p className="text-neutral-300 text-sm">{selectedData.economicDrivers}</p>
            </div>
            <div>
              <h5 className="text-sm font-medium text-cyan-400 mb-2">Seasonal Trends</h5>
              <p className="text-neutral-300 text-sm">{selectedData.seasonalTrends}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Strategy Details */}
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <h4 className="text-lg font-semibold text-white mb-4">Strategy Configuration</h4>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <h5 className="text-sm font-medium text-purple-400 mb-2">Strategy Type</h5>
              <p className="text-green-400 font-semibold text-lg">{selectedData.strategy}</p>
              <p className="text-neutral-300 text-sm mt-1">{selectedData.strategyDetails}</p>
            </div>
            <div>
              <h5 className="text-sm font-medium text-blue-400 mb-2">Signal Generation</h5>
              <p className="text-neutral-300 text-sm">
                Frequency:{' '}
                <span className="text-cyan-400 font-medium">
                  {selectedData.strategyParams.signalFreq}
                </span>
              </p>
              <p className="text-neutral-300 text-sm">
                Min R/R:{' '}
                <span className="text-cyan-400 font-medium">
                  {selectedData.strategyParams.riskReward}
                </span>
              </p>
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <h5 className="text-sm font-medium text-red-400 mb-2">Risk Management</h5>
              <p className="text-neutral-300 text-sm">
                Stop Loss:{' '}
                <span className="text-red-400 font-medium">
                  {selectedData.strategyParams.stopLoss}
                </span>
              </p>
              <p className="text-neutral-300 text-sm">
                Take Profit:{' '}
                <span className="text-green-400 font-medium">
                  {selectedData.strategyParams.takeProfit}
                </span>
              </p>
            </div>
            <div>
              <h5 className="text-sm font-medium text-yellow-400 mb-2">Risk Classification</h5>
              <p className={`font-semibold ${getRiskColor(selectedData.riskProfile)}`}>
                {selectedData.riskProfile}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Trading Recommendations */}
      <div className="bg-neutral-900 border border-neutral-600 rounded-lg p-6">
        <h4 className="text-lg font-semibold text-white mb-4">Trading Recommendations</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div>
            <h5 className="text-sm font-medium text-yellow-400 mb-2">Position Sizing</h5>
            <p className="text-neutral-300 text-sm">
              {selectedData.riskProfile === 'Low' && 'Standard 2% risk per trade acceptable'}
              {selectedData.riskProfile === 'Moderate' && 'Standard 2% risk, monitor correlation'}
              {selectedData.riskProfile === 'Moderate-High' &&
                'Reduce to 1.5% risk during volatility'}
              {selectedData.riskProfile === 'High' && 'Maximum 1% risk, experienced traders only'}
            </p>
          </div>
          <div>
            <h5 className="text-sm font-medium text-green-400 mb-2">ATR Settings</h5>
            <p className="text-neutral-300 text-sm">
              {selectedData.riskProfile === 'Low' && '2.0x stop loss, 3.0x take profit'}
              {selectedData.riskProfile === 'Moderate' && '2.5x stop loss, 3.5x take profit'}
              {selectedData.riskProfile === 'Moderate-High' && '2.5x stop loss, 4.0x take profit'}
              {selectedData.riskProfile === 'High' && '3.0x stop loss, 4.5x take profit'}
            </p>
          </div>
          <div>
            <h5 className="text-sm font-medium text-blue-400 mb-2">Portfolio Allocation</h5>
            <p className="text-neutral-300 text-sm">
              {selectedData.allocation === 'Primary' && '25% of core allocation'}
              {selectedData.allocation === 'Core Position' && '20% of core allocation'}
              {selectedData.allocation === 'Diversification' && '15% of core allocation'}
              {selectedData.allocation === 'Secondary' && '15% of diversification'}
              {selectedData.allocation === 'Portfolio Balance' && '10% of diversification'}
              {selectedData.allocation === 'Complementary' && '10% of diversification'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

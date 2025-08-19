'use client';

/**
 * Mock Data for Testing Backtest Dashboard
 *
 * This provides fallback data when the backend API is not available
 * Useful for frontend development and testing
 */

export const mockSummaryData = {
  total_strategies: 276,
  avg_annual_return: 0.24,
  avg_max_drawdown: -0.12,
  avg_sharpe_ratio: 1.85,
  winning_percentage: 0.68,
  timeframe: '2019-2024 (5 years)',
  currency_pairs: ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD'],
};

export const mockPerformanceData = {
  annual_return: 0.24,
  total_return: 1.85,
  max_drawdown: -0.12,
  sharpe_ratio: 1.85,
  calmar_ratio: 2.0,
  volatility: 0.15,
  total_trades: 2845,
  win_rate: 0.68,
  avg_win: 125.5,
  avg_loss: -85.25,
  profit_factor: 1.72,
};

export const mockEquityData = [
  { date: '2019-01-01', equity: 10000, drawdown: 0 },
  { date: '2019-03-01', equity: 10250, drawdown: 0 },
  { date: '2019-06-01', equity: 10380, drawdown: -0.02 },
  { date: '2019-09-01', equity: 10650, drawdown: 0 },
  { date: '2019-12-01', equity: 10890, drawdown: 0 },
  { date: '2020-03-01', equity: 10650, drawdown: -0.08 },
  { date: '2020-06-01', equity: 11200, drawdown: 0 },
  { date: '2020-09-01', equity: 11450, drawdown: 0 },
  { date: '2020-12-01', equity: 11780, drawdown: 0 },
  { date: '2021-03-01', equity: 12100, drawdown: 0 },
  { date: '2021-06-01', equity: 12350, drawdown: 0 },
  { date: '2021-09-01', equity: 12200, drawdown: -0.05 },
  { date: '2021-12-01', equity: 12650, drawdown: 0 },
  { date: '2022-03-01', equity: 13100, drawdown: 0 },
  { date: '2022-06-01', equity: 12890, drawdown: -0.07 },
  { date: '2022-09-01', equity: 13250, drawdown: 0 },
  { date: '2022-12-01', equity: 13580, drawdown: 0 },
  { date: '2023-03-01', equity: 14100, drawdown: 0 },
  { date: '2023-06-01', equity: 14520, drawdown: 0 },
  { date: '2023-09-01', equity: 14350, drawdown: -0.04 },
  { date: '2023-12-01', equity: 14890, drawdown: 0 },
  { date: '2024-03-01', equity: 15200, drawdown: 0 },
  { date: '2024-06-01', equity: 15650, drawdown: 0 },
  { date: '2024-08-19', equity: 16120, drawdown: 0 },
];

export const mockVisualData = [
  {
    title: 'Monthly Performance Heatmap',
    description: 'Monthly returns visualization showing seasonal patterns and consistency',
    chart_type: 'heatmap',
    data: {
      '2019': {
        Jan: 2.5,
        Feb: 1.8,
        Mar: 3.2,
        Apr: 2.1,
        May: 1.5,
        Jun: 2.8,
        Jul: 3.5,
        Aug: 2.2,
        Sep: 1.9,
        Oct: 3.1,
        Nov: 2.4,
        Dec: 2.7,
      },
      '2020': {
        Jan: 1.2,
        Feb: -2.5,
        Mar: -4.8,
        Apr: 5.2,
        May: 3.8,
        Jun: 4.1,
        Jul: 2.9,
        Aug: 1.8,
        Sep: 2.5,
        Oct: 1.7,
        Nov: 3.2,
        Dec: 2.8,
      },
      '2021': {
        Jan: 3.1,
        Feb: 2.8,
        Mar: 2.5,
        Apr: 1.9,
        May: 2.2,
        Jun: 2.0,
        Jul: 1.8,
        Aug: 2.4,
        Sep: -1.2,
        Oct: 2.8,
        Nov: 3.5,
        Dec: 3.7,
      },
      '2022': {
        Jan: 2.8,
        Feb: 2.2,
        Mar: 3.6,
        Apr: 1.8,
        May: 2.1,
        Jun: -1.6,
        Jul: 2.9,
        Aug: 1.5,
        Sep: 3.2,
        Oct: 2.4,
        Nov: 2.7,
        Dec: 2.5,
      },
      '2023': {
        Jan: 3.8,
        Feb: 3.2,
        Mar: 3.9,
        Apr: 2.5,
        May: 2.8,
        Jun: 3.1,
        Jul: 2.7,
        Aug: 2.2,
        Sep: -1.2,
        Oct: 3.5,
        Nov: 3.8,
        Dec: 3.6,
      },
      '2024': { Jan: 2.5, Feb: 2.8, Mar: 3.2, Apr: 2.1, May: 2.4, Jun: 2.9, Jul: 3.1, Aug: 2.2 },
    },
  },
  {
    title: 'Drawdown Analysis',
    description: 'Analysis of drawdown periods and recovery times',
    chart_type: 'line',
    data: [
      { period: '2020-Q1', drawdown: -8.2, recovery_days: 45 },
      { period: '2021-Q3', drawdown: -5.1, recovery_days: 28 },
      { period: '2022-Q2', drawdown: -7.3, recovery_days: 38 },
      { period: '2023-Q3', drawdown: -4.2, recovery_days: 21 },
    ],
  },
  {
    title: 'Strategy Distribution',
    description: 'Distribution of strategies by performance quartiles',
    chart_type: 'pie',
    data: {
      'Top Quartile (>30% Annual)': 69,
      'Second Quartile (20-30%)': 83,
      'Third Quartile (10-20%)': 78,
      'Bottom Quartile (<10%)': 46,
    },
  },
  {
    title: 'Risk-Return Scatter',
    description: 'Risk vs Return analysis across all tested strategies',
    chart_type: 'scatter',
    data: [
      { risk: 0.12, return: 0.28, strategies: 15 },
      { risk: 0.15, return: 0.24, strategies: 42 },
      { risk: 0.18, return: 0.31, strategies: 38 },
      { risk: 0.22, return: 0.19, strategies: 28 },
      { risk: 0.25, return: 0.35, strategies: 22 },
    ],
  },
];

export const mockMethodologyData = [
  {
    title: 'Strategy Overview',
    content:
      'The MA Unified Strategy employs a sophisticated multi-timeframe moving average approach, combining trend detection with adaptive position sizing. The strategy utilizes exponential moving averages (EMA) across 5, 13, 21, 55, and 89-period windows to identify optimal entry and exit points.',
    section: 'overview',
  },
  {
    title: 'Moving Average Configuration',
    content:
      'Primary trend identification uses the 21/55 EMA crossover system, while short-term signals are generated through 5/13 EMA interactions. The 89 EMA serves as a long-term trend filter, ensuring trades align with the broader market direction.',
    section: 'technical_indicators',
  },
  {
    title: 'Entry Rules',
    content:
      'Long positions are initiated when: 1) 5 EMA crosses above 13 EMA, 2) Price is above 21 EMA, 3) 21 EMA is above 55 EMA, 4) Overall trend confirmed by 89 EMA direction. Additional confluence factors include volume confirmation and momentum indicators.',
    section: 'entry_exit_rules',
  },
  {
    title: 'Exit Rules',
    content:
      'Positions are closed when: 1) 5 EMA crosses below 13 EMA, 2) Price closes below 21 EMA for 2 consecutive periods, 3) Stop-loss triggered at 2% adverse move, 4) Take-profit achieved at 4% favorable move, or 5) Maximum position hold time of 72 hours reached.',
    section: 'entry_exit_rules',
  },
  {
    title: 'Position Sizing',
    content:
      'Dynamic position sizing based on volatility-adjusted risk parity. Base position size is 2% of account equity, adjusted by 14-period ATR. Maximum position size capped at 5% of account. Risk is further managed through correlation limits across currency pairs.',
    section: 'risk_management',
  },
  {
    title: 'Stop Loss Management',
    content:
      'Initial stop-loss set at 2x ATR from entry price. Trailing stop activates after 1.5% favorable move, trailing at 1x ATR distance. Stop-loss levels are adjusted for market session volatility and major news events.',
    section: 'risk_management',
  },
  {
    title: 'Backtesting Framework',
    content:
      'Comprehensive backtesting performed using tick-level data from 2019-2024. Out-of-sample testing covers the final 12 months. Walk-forward optimization ensures parameter stability across different market regimes.',
    section: 'backtesting_methodology',
  },
  {
    title: 'Data Quality Assurance',
    content:
      'All price data validated for gaps, spikes, and inconsistencies. Spread costs and slippage modeled based on historical order book data. Realistic execution assumptions include 0.5-2 pip spread depending on currency pair and market conditions.',
    section: 'backtesting_methodology',
  },
  {
    title: 'Performance Metrics Calculation',
    content:
      'Sharpe ratio calculated using risk-free rate of 2% annually. Calmar ratio uses maximum drawdown over entire test period. All returns are compound annual growth rates (CAGR). Win rate excludes break-even trades (±0.1% threshold).',
    section: 'performance_metrics',
  },
  {
    title: 'Risk Metrics',
    content:
      'Maximum drawdown calculated from peak to trough equity values. Value at Risk (VaR) estimated using 95% confidence interval over 30-day rolling windows. Correlation analysis performed across all active positions to limit portfolio concentration risk.',
    section: 'performance_metrics',
  },
  {
    title: 'Implementation Architecture',
    content:
      'Strategy implemented using Python with pandas for data processing and NumPy for mathematical calculations. Real-time execution framework built on asyncio for concurrent order management. Database integration with PostgreSQL for trade logging and performance tracking.',
    section: 'implementation_details',
  },
  {
    title: 'Production Deployment',
    content:
      'Live trading system deployed on cloud infrastructure with 99.9% uptime SLA. Redundant data feeds from multiple providers ensure continuous market coverage. Automated monitoring and alerting system tracks strategy performance and system health metrics.',
    section: 'implementation_details',
  },
];

/**
 * Helper function to simulate API delay
 */
export const simulateApiDelay = (ms: number = 500) =>
  new Promise(resolve => setTimeout(resolve, ms));

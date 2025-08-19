/**
 * Local Backtest Data Loader
 * Loads backtest data from local JSON files instead of API calls
 */

export interface BacktestSummary {
  hero_metrics: {
    top_annual_return: string;
    top_sharpe_ratio: number;
    max_drawdown: string;
    win_rate: string;
    strategies_analyzed: number;
    data_period: string;
  };
  top_3_strategies: Array<{
    rank: number;
    execution_id: string;
    currency_pair: string;
    strategy: string;
    timeframe: string;
    performance_metrics: {
      annual_return: number;
      annual_return_pct: string;
      sharpe_ratio: number;
      max_drawdown: number;
      max_drawdown_pct: string;
      win_rate: number;
      win_rate_pct: string;
    };
    category: string;
    description: string;
  }>;
  last_updated: string;
}

export interface PerformanceData {
  total_strategies_analyzed: number;
  top_performing_strategies: Array<{
    rank: number;
    execution_id: string;
    currency_pair: string;
    strategy: string;
    timeframe: string;
    performance_metrics: {
      annual_return: number;
      annual_return_pct: string;
      sharpe_ratio: number;
      max_drawdown: number;
      max_drawdown_pct: string;
      win_rate: number;
      win_rate_pct: string;
    };
    category: string;
    description: string;
  }>;
  performance_summary: {
    annual_return_range: string;
    sharpe_ratio_range: string;
    max_drawdown_range: string;
    win_rate_range: string;
    best_timeframe: string;
    best_pairs: string[];
    preferred_risk_profile: string;
  };
}

export interface EquityCurveData {
  generated_date: string;
  initial_balance: number;
  period: string;
  frequency: string;
  total_weeks: number;
  equity_curves: {
    [strategyId: string]: {
      dates: string[];
      equity_values: number[];
      final_equity?: number;
      total_return?: number;
      max_drawdown?: number;
    };
  };
}

export interface VisualDatasets {
  generated_date: string;
  purpose: string;
  phase: string;
  datasets: {
    monthly_heatmap: any;
    risk_return_scatter: any;
    drawdown_analysis: any;
    comparison_matrix: any;
    win_rate_analysis: any;
  };
}

// Data cache to avoid multiple loads
let dataCache: {
  topStrategies?: any;
  equityCurves?: any;
  visualDatasets?: any;
} = {};

/**
 * Load top strategies data
 */
async function loadTopStrategiesData() {
  if (dataCache.topStrategies) return dataCache.topStrategies;

  try {
    const response = await fetch('/backtest_data/top_strategies_performance.json');
    dataCache.topStrategies = await response.json();
    return dataCache.topStrategies;
  } catch (error) {
    console.error('Failed to load top strategies data:', error);
    throw error;
  }
}

/**
 * Load equity curves data
 */
async function loadEquityCurvesData() {
  if (dataCache.equityCurves) return dataCache.equityCurves;

  try {
    const response = await fetch('/backtest_data/equity_curves.json');
    dataCache.equityCurves = await response.json();
    return dataCache.equityCurves;
  } catch (error) {
    console.error('Failed to load equity curves data:', error);
    throw error;
  }
}

/**
 * Load visual datasets data
 */
async function loadVisualDatasetsData() {
  if (dataCache.visualDatasets) return dataCache.visualDatasets;

  try {
    const response = await fetch('/backtest_data/visual_datasets/all_visual_datasets.json');
    dataCache.visualDatasets = await response.json();
    return dataCache.visualDatasets;
  } catch (error) {
    console.error('Failed to load visual datasets data:', error);
    throw error;
  }
}

/**
 * Generate backtest summary from top strategies data
 */
export async function getBacktestSummary(): Promise<BacktestSummary> {
  const topStrategiesData = await loadTopStrategiesData();
  const topStrategies = topStrategiesData.top_performing_strategies.slice(0, 3);

  // Calculate hero metrics from all strategies
  const allStrategies = topStrategiesData.top_performing_strategies;
  const topAnnualReturn = Math.max(
    ...allStrategies.map((s: any) => s.performance_metrics.annual_return)
  );
  const topSharpeRatio = Math.max(
    ...allStrategies.map((s: any) => s.performance_metrics.sharpe_ratio)
  );
  const minDrawdown = Math.min(
    ...allStrategies.map((s: any) => s.performance_metrics.max_drawdown)
  );
  const avgWinRate =
    allStrategies.reduce((sum: number, s: any) => sum + s.performance_metrics.win_rate, 0) /
    allStrategies.length;

  return {
    hero_metrics: {
      top_annual_return: `${(topAnnualReturn * 100).toFixed(1)}%`,
      top_sharpe_ratio: topSharpeRatio,
      max_drawdown: `${(minDrawdown * 100).toFixed(1)}%`,
      win_rate: `${(avgWinRate * 100).toFixed(1)}%`,
      strategies_analyzed: topStrategiesData.total_strategies_analyzed,
      data_period: '5 Years (2020-2025)',
    },
    top_3_strategies: topStrategies,
    last_updated: topStrategiesData.extraction_date,
  };
}

/**
 * Get performance data from top strategies
 */
export async function getPerformanceData(): Promise<PerformanceData> {
  const topStrategiesData = await loadTopStrategiesData();
  const allStrategies = topStrategiesData.top_performing_strategies;

  // Calculate performance summary
  const annualReturns = allStrategies.map((s: any) => s.performance_metrics.annual_return);
  const sharpeRatios = allStrategies.map((s: any) => s.performance_metrics.sharpe_ratio);
  const drawdowns = allStrategies.map((s: any) => s.performance_metrics.max_drawdown);
  const winRates = allStrategies.map((s: any) => s.performance_metrics.win_rate);

  // Find best timeframe (most frequent in top 10)
  const timeframes = allStrategies.slice(0, 10).map((s: any) => s.timeframe);
  const timeframeCounts = timeframes.reduce((acc: Record<string, number>, tf: string) => {
    acc[tf] = (acc[tf] || 0) + 1;
    return acc;
  }, {});
  const bestTimeframe = Object.entries(timeframeCounts).sort(
    ([, a], [, b]) => (b as number) - (a as number)
  )[0][0];

  // Find best pairs (most frequent in top 10)
  const pairs = allStrategies.slice(0, 10).map((s: any) => s.currency_pair);
  const pairCounts = pairs.reduce((acc: Record<string, number>, pair: string) => {
    acc[pair] = (acc[pair] || 0) + 1;
    return acc;
  }, {});
  const bestPairs = Object.entries(pairCounts)
    .sort(([, a], [, b]) => (b as number) - (a as number))
    .slice(0, 3)
    .map(([pair]) => pair);

  return {
    total_strategies_analyzed: topStrategiesData.total_strategies_analyzed,
    top_performing_strategies: allStrategies,
    performance_summary: {
      annual_return_range: `${(Math.min(...annualReturns) * 100).toFixed(1)}% - ${(
        Math.max(...annualReturns) * 100
      ).toFixed(1)}%`,
      sharpe_ratio_range: `${Math.min(...sharpeRatios).toFixed(2)} - ${Math.max(
        ...sharpeRatios
      ).toFixed(2)}`,
      max_drawdown_range: `${(Math.min(...drawdowns) * 100).toFixed(1)}% - ${(
        Math.max(...drawdowns) * 100
      ).toFixed(1)}%`,
      win_rate_range: `${(Math.min(...winRates) * 100).toFixed(1)}% - ${(
        Math.max(...winRates) * 100
      ).toFixed(1)}%`,
      best_timeframe: bestTimeframe,
      best_pairs: bestPairs,
      preferred_risk_profile: 'Conservative to Moderate',
    },
  };
}

/**
 * Get equity curve data
 */
export async function getEquityCurveData(): Promise<EquityCurveData> {
  return await loadEquityCurvesData();
}

/**
 * Get visual datasets
 */
export async function getVisualDatasets(): Promise<VisualDatasets> {
  const visualData = await loadVisualDatasetsData();

  // Load individual visual dataset files
  const [riskReturnData, drawdownData, comparisonData, winRateData] = await Promise.all([
    fetch('/backtest_data/visual_datasets/risk_return_scatter.json')
      .then(r => r.json())
      .catch(error => {
        console.error('Failed to load risk_return_scatter.json:', error);
        return null;
      }),
    fetch('/backtest_data/visual_datasets/drawdown_analysis.json')
      .then(r => r.json())
      .catch(error => {
        console.error('Failed to load drawdown_analysis.json:', error);
        return null;
      }),
    fetch('/backtest_data/visual_datasets/comparison_matrix.json')
      .then(r => r.json())
      .catch(error => {
        console.error('Failed to load comparison_matrix.json:', error);
        return null;
      }),
    fetch('/backtest_data/visual_datasets/win_rate_analysis.json')
      .then(r => r.json())
      .catch(error => {
        console.error('Failed to load win_rate_analysis.json:', error);
        return null;
      }),
  ]);

  console.log('Loaded visual datasets:', {
    monthly_heatmap: !!visualData.datasets.monthly_heatmap,
    risk_return_scatter: !!riskReturnData,
    drawdown_analysis: !!drawdownData,
    comparison_matrix: !!comparisonData,
    win_rate_analysis: !!winRateData,
  });

  return {
    generated_date: visualData.generated_date,
    purpose: visualData.purpose,
    phase: visualData.phase,
    datasets: {
      monthly_heatmap: visualData.datasets.monthly_heatmap,
      risk_return_scatter: riskReturnData,
      drawdown_analysis: drawdownData,
      comparison_matrix: comparisonData,
      win_rate_analysis: winRateData,
    },
  };
}

/**
 * Simulate API delay for consistent UX
 */
export function simulateApiDelay(ms: number = 500): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

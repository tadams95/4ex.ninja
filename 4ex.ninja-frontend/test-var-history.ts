// Test script for VaR History Hook
// This will be removed after testing

import { useVaRHistory } from '../src/hooks/useRiskData';

console.log('Testing VaR History Hook...');

// Test different periods
const periods = ['1D', '1W', '1M'];

// This is just a TypeScript validation test
// The actual runtime testing will be done in the component
export const testVaRHistoryTypes = () => {
  // This should compile without errors if our types are correct
  const result = useVaRHistory('1D', 300000);

  // Type checking
  if (result.historyData) {
    const point = result.historyData.data[0];
    const summary = result.historyData.summary;

    console.log('Point structure:', {
      timestamp: point.timestamp,
      parametric: point.parametric,
      historical: point.historical,
      monte_carlo: point.monte_carlo,
      target: point.target,
    });

    console.log('Summary structure:', {
      total_points: summary.total_points,
      breaches_count: summary.breaches_count,
      avg_var: summary.avg_var,
      max_var: summary.max_var,
      min_var: summary.min_var,
    });
  }

  return result;
};

console.log('✅ VaR History Hook types validated');

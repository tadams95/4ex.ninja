// Quick test of the second backtest data loader
import { loadEnhancedOptimizationResults } from '../src/lib/secondBacktestDataLoader';

async function testLoader() {
  try {
    console.log('Testing second backtest data loader...');
    const data = await loadEnhancedOptimizationResults();
    console.log('✅ Data loaded successfully');
    console.log('Total pairs:', data.optimization_info.total_pairs_tested);
    console.log('Total trades:', data.optimization_info.total_trades);
    console.log('Success rate:', data.optimization_info.success_rate);
    console.log('Strategy version:', data.optimization_info.strategy_version);
    console.log('Top performer:', data.summary_stats.top_performer);
    console.log('Profitable pairs:', Object.keys(data.profitable_pairs).length);
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

testLoader();

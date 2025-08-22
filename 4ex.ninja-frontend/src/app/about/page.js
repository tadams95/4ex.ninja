export default function AboutPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-4xl font-bold mb-8">About 4ex.ninja</h1>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Our Enhanced Daily EMA Strategy</h2>
        <p className="text-gray-300 mb-4">
          4ex.ninja delivers sophisticated forex trading insights through our Enhanced Daily EMA
          Strategy, a comprehensively optimized dual exponential moving average crossover system.
          Through extensive backtesting across 10 major currency pairs, we've discovered key market
          insights that inform our targeted approach to algorithmic forex trading recommendations.
        </p>
        <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4 mb-4">
          <p className="text-blue-300 text-sm">
            <strong>Key Discovery:</strong> Our August 2025 optimization revealed JPY pairs
            significantly outperform traditional majors, with USD_JPY achieving 14.0% annual returns
            and 70% win rate, while EUR_USD showed -4.6% returns despite being the world's most
            traded pair.
          </p>
        </div>
        <div className="bg-green-900/20 border border-green-700 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-green-400 font-semibold mb-1">
                📊 View Complete Backtest Results
              </h3>
              <p className="text-green-300 text-sm">
                Explore detailed performance data, methodology, and comprehensive analysis of our
                10-pair optimization study including interactive charts and strategy documentation.
              </p>
            </div>
            <a
              href="/backtest"
              className="ml-4 px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-colors whitespace-nowrap"
            >
              View Results →
            </a>
          </div>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Comprehensive Optimization Results</h2>
        <p className="text-gray-300 mb-4">
          Our strategy underwent rigorous testing across 10 major forex pairs, revealing a realistic
          50% success rate with significant JPY pair dominance. This data-driven approach ensures
          our recommendations are based on verified performance rather than theoretical models.
        </p>

        <div className="bg-neutral-800 border border-neutral-600 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-3">Key Findings Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-green-400 font-semibold">✅ Profitable Strategies (5)</div>
              <p className="text-gray-300 mt-1">
                JPY pairs demonstrated superior trend-following characteristics with consistently
                higher win rates
              </p>
            </div>
            <div>
              <div className="text-red-400 font-semibold">❌ Avoided Strategies (5)</div>
              <p className="text-gray-300 mt-1">
                Traditional major pairs underperformed expectations, including EUR_USD despite high
                liquidity
              </p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-neutral-600">
            <p className="text-blue-300 text-sm">
              <strong>
                Complete performance breakdown, methodology details, and interactive analysis
                available in our backtest results.
              </strong>
            </p>
          </div>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-4">How Our Enhanced Strategy Works</h2>
        <div className="space-y-4">
          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-xl font-bold mb-2">Dual EMA Crossover System</h3>
            <p className="text-gray-300">
              Our core strategy employs optimized exponential moving average configurations (EMA
              20/60 and EMA 30/60) on daily timeframes, with pair-specific parameters determined
              through comprehensive backtesting to maximize effectiveness across different currency
              characteristics.
            </p>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-xl font-bold mb-2">Enhanced Signal Processing</h3>
            <p className="text-gray-300">
              Beyond basic crossovers, our system incorporates session-based filtering (prioritizing
              JPY pairs during Asian sessions), support/resistance confluence detection, and dynamic
              position sizing based on signal strength and market volatility for improved trade
              selection.
            </p>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-xl font-bold mb-2">Realistic Risk Management</h3>
            <p className="text-gray-300">
              Each recommendation includes calculated risk parameters with fixed 1.5% stop loss and
              3.0% take profit levels (2:1 reward-to-risk ratio). Our models incorporate realistic
              trading costs (20-40 pip spreads) to ensure recommendations remain profitable after
              real-world execution expenses.
            </p>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-xl font-bold mb-2">JPY Pair Specialization</h3>
            <p className="text-gray-300">
              Our optimization revealed JPY pairs demonstrate superior trend-following
              characteristics, with 4 out of 5 profitable strategies involving the Japanese Yen. We
              provide specialized timing recommendations for JPY pairs during optimal Asian trading
              sessions for maximum effectiveness.
            </p>
          </div>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Performance Expectations</h2>
        <div className="bg-neutral-800 border border-neutral-600 rounded-lg p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">50%</div>
              <div className="text-sm text-gray-400">Success Rate</div>
              <div className="text-xs text-gray-500">Realistic expectations</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">10-15</div>
              <div className="text-sm text-gray-400">Trades/Year</div>
              <div className="text-xs text-gray-500">Quality over quantity</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-400">JPY</div>
              <div className="text-sm text-gray-400">Pair Focus</div>
              <div className="text-xs text-gray-500">Superior performance</div>
            </div>
          </div>
          <p className="text-gray-300 text-sm">
            Our optimization revealed moderate trade frequency focusing on high-probability setups,
            with demonstrated JPY pair outperformance during favorable market conditions. Detailed
            performance metrics and allocation recommendations available in our backtest analysis.
          </p>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Strategy Transparency</h2>
        <p className="text-gray-300 mb-4">
          Unlike traditional "black box" systems, our Enhanced Daily EMA Strategy provides complete
          transparency through detailed backtesting results, methodology documentation, and
          performance attribution analysis. Every recommendation is backed by verified optimization
          data and realistic cost modeling.
        </p>
        <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
          <p className="text-yellow-300 text-sm">
            <strong>Important:</strong> Our optimization period captured specific market conditions
            favoring JPY trend-following. Performance may vary under different market regimes,
            particularly during central bank intervention periods or significant shifts in global
            risk sentiment.
          </p>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Risk Disclosure</h2>
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
          <p className="text-red-200 text-sm mb-3">
            <strong>Important Risk Warning:</strong> Forex trading involves substantial risks and
            may result in significant financial losses. Past performance does not guarantee future
            results.
          </p>
          <ul className="text-red-200 text-sm space-y-1">
            <li>• Our 50% success rate means 50% of strategies showed negative returns</li>
            <li>
              • JPY pair strategies may underperform during Bank of Japan intervention periods
            </li>
            <li>• Trading costs significantly impact lower-return strategies</li>
            <li>• Maximum expected portfolio drawdowns of 8-12% during adverse conditions</li>
            <li>• All recommendations are for informational purposes only</li>
          </ul>
          <p className="text-red-200 text-sm mt-3">
            Always exercise prudent risk management, never risk more than 1% per trade, and avoid
            trading with funds you cannot afford to lose. Consider our insights as part of a
            comprehensive trading plan rather than standalone investment advice.
          </p>
        </div>
      </section>
    </div>
  );
}

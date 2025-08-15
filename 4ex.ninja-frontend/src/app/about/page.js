export default function AboutPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <h1 className="text-4xl font-bold mb-8">About 4ex.ninja</h1>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Our Approach</h2>
        <p className="text-gray-300 mb-4">
          4ex.ninja delivers algorithmic forex trading insights based on proven technical analysis
          strategies. Our recommendations are generated using sophisticated Moving Average crossover
          systems, tested across multiple timeframes and currency pairs.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-4">How It Works</h2>
        <div className="space-y-4">
          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-xl font-bold mb-2">Automated Analysis</h3>
            <p className="text-gray-300">
              Our algorithms continuously monitor major forex pairs on H4 and Daily timeframes,
              identifying high-probability trading opportunities using advanced Moving Average
              strategies.
            </p>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-xl font-bold mb-2">Real-Time Insights</h3>
            <p className="text-gray-300">
              When our system identifies a potential trade setup, subscribers receive detailed
              recommendations including suggested entry price, stop loss, and take profit levels to
              inform their trading decisions.
            </p>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-xl font-bold mb-2">Risk Management Guidance</h3>
            <p className="text-gray-300">
              Each recommendation includes calculated stop loss and take profit levels, designed to
              support consistent risk management as part of your broader trading strategy.
            </p>
          </div>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Disclaimer</h2>
        <p className="text-gray-300 text-sm">
          Forex trading involves substantial risks and may result in significant financial losses.
          Past performance does not guarantee future results. Our insights and recommendations are
          provided for informational purposes only and should be used as part of a comprehensive
          trading plan. Always exercise prudent risk management and avoid trading with funds you
          cannot afford to lose.
        </p>
      </section>
    </div>
  );
}

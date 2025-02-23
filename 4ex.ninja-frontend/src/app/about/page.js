export default function AboutPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <h1 className="text-4xl font-bold mb-8">About 4ex.ninja</h1>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Our Approach</h2>
        <p className="text-gray-300 mb-4">
          4ex.ninja delivers algorithmic forex trading signals based on proven
          technical analysis strategies. Our signals are generated using
          sophisticated Moving Average crossover systems, tested across multiple
          timeframes and currency pairs.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-4">How It Works</h2>
        <div className="space-y-4">
          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-xl font-bold mb-2">Automated Analysis</h3>
            <p className="text-gray-300">
              Our algorithms continuously monitor major forex pairs on H4 and
              Daily timeframes, identifying high-probability trading
              opportunities using Moving Average strategies.
            </p>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-xl font-bold mb-2">Real-Time Signals</h3>
            <p className="text-gray-300">
              When our system detects a potential trade setup, subscribers
              receive detailed signals including entry price, stop loss, and
              take profit levels.
            </p>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-xl font-bold mb-2">Risk Management</h3>
            <p className="text-gray-300">
              Each signal comes with calculated stop loss and take profit
              levels, helping you maintain consistent risk management in your
              trading.
            </p>
          </div>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Disclaimer</h2>
        <p className="text-gray-300 text-sm">
          Trading forex carries significant risks. Past performance is not
          indicative of future results. Our signals should be used as part of a
          comprehensive trading strategy. Always manage your risk and never
          trade with money you cannot afford to lose.
        </p>
      </section>
    </div>
  );
}

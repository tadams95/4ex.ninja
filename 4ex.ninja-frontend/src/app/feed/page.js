export default function SignalsPage() {
  // Dummy signals data
  const dummySignals = [
    {
      _id: "1",
      pair: "EUR/USD",
      type: "BUY",
      entry: "1.0890",
      stopLoss: "1.0850",
      takeProfit: "1.0950",
      timestamp: "2024-02-23T14:30:00Z",
      status: "ACTIVE",
    },
    {
      _id: "2",
      pair: "GBP/USD",
      type: "SELL",
      entry: "1.2650",
      stopLoss: "1.2690",
      takeProfit: "1.2590",
      timestamp: "2024-02-23T13:15:00Z",
      status: "ACTIVE",
    },
    {
      _id: "3",
      pair: "USD/JPY",
      type: "BUY",
      entry: "150.30",
      stopLoss: "150.00",
      takeProfit: "150.90",
      timestamp: "2024-02-23T12:45:00Z",
      status: "ACTIVE",
    },
    {
      _id: "4",
      pair: "AUD/USD",
      type: "SELL",
      entry: "0.7700",
      stopLoss: "0.7740",
      takeProfit: "0.7660",
      timestamp: "2024-02-23T11:30:00Z",
      status: "ACTIVE",
    },
  ];

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl bg-black">
      <h1 className="text-3xl font-bold mb-6">Latest Forex Signals</h1>
      <div className="space-y-4">
        {dummySignals.map((signal) => (
          <div
            key={signal._id}
            className={`bg-gray-700 rounded-lg p-6 shadow-lg border-l-4 ${
              signal.type === "BUY" ? "border-green-500" : "border-red-500"
            }`}
          >
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">{signal.pair}</h2>
              <span
                className={`px-3 py-1 rounded-full text-sm ${
                  signal.type === "BUY"
                    ? "bg-green-500/20 text-green-400"
                    : "bg-red-500/20 text-red-400"
                }`}
              >
                {signal.type}
              </span>
            </div>
            <div className="space-y-2">
              <p className="text-gray-300">Entry: {signal.entry}</p>
              <p className="text-gray-300">Stop Loss: {signal.stopLoss}</p>
              <p className="text-gray-300">Take Profit: {signal.takeProfit}</p>
              <p className="text-sm text-gray-400 mt-4">
                {new Date(signal.timestamp).toLocaleString()}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

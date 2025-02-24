"use client";

import { motion } from "framer-motion";
import { useState, useEffect, useRef } from "react";

const pairs = [
  { pair: "EUR/USD", value: "1.0921" },
  { pair: "GBP/USD", value: "1.2634" },
  { pair: "USD/JPY", value: "107.23" },
  { pair: "USD/CHF", value: "0.9612" },
  { pair: "EUR/GBP", value: "0.8641" },
  { pair: "EUR/JPY", value: "117.23" },
  { pair: "GBP/JPY", value: "135.23" },
  { pair: "USD/CAD", value: "1.3634" },
  { pair: "AUD/USD", value: "0.6923" },
  { pair: "NZD/USD", value: "0.6423" },
  { pair: "EUR/CHF", value: "0.9723" },
  { pair: "AUD/CAD", value: "0.9134" },
  { pair: "GBP/CHF", value: "1.1234" },
  { pair: "USD/SEK", value: "10.4521" },
  { pair: "USD/NOK", value: "10.2341" },
];

export default function CurrencyTicker() {
  const [prices, setPrices] = useState(pairs);
  const containerRef = useRef(null);
  const [containerWidth, setContainerWidth] = useState(0);

  useEffect(() => {
    // Using Finnhub WebSocket for streaming prices
    const socket = new WebSocket(
      "wss://ws.finnhub.io?token=cutvmf1r01qv6ijkok70cutvmf1r01qv6ijkok7g"
    );

    socket.addEventListener("open", () => {
      // Finnhub uses symbols like "OANDA:EUR_USD" so adjust accordingly if needed.
      pairs.forEach(({ pair }) => {
        const symbol = "OANDA:" + pair.replace("/", "_");
        socket.send(JSON.stringify({ type: "subscribe", symbol }));
      });
    });

    socket.addEventListener("message", (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "trade") {
        // Find updates for the pairs
        data.data.forEach((trade) => {
          // Convert symbol back if needed: "OANDA:EUR_USD" -> "EUR/USD"
          const pair = trade.s.split(":")[1].replace("_", "/");
          setPrices((prev) =>
            prev.map((p) => {
              if (p.pair === pair) {
                // Optional: You can see if the new price increased or decreased.
                const newValue = trade.p.toFixed(4);
                const isIncreased =
                  Number.parseFloat(newValue) > Number.parseFloat(p.value);
                return { ...p, value: newValue, increased: isIncreased };
              }
              return p;
            })
          );
        });
      }
    });

    const updateContainerWidth = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.scrollWidth / 2);
      }
    };

    updateContainerWidth();
    window.addEventListener("resize", updateContainerWidth);

    return () => {
      socket.close();
      window.removeEventListener("resize", updateContainerWidth);
    };
  }, []);

  return (
    <div className="w-full overflow-hidden bg-black py-2 pt-4">
      <motion.div
        ref={containerRef}
        className="flex space-x-8"
        animate={{
          x: [-containerWidth, 0],
        }}
        transition={{
          x: {
            repeat: Number.POSITIVE_INFINITY,
            repeatType: "loop",
            duration: 50,
            ease: "linear",
          },
        }}
      >
        {[...prices, ...prices].map((item, index) => (
          <motion.div
            key={`${item.pair}-${index}`}
            className="flex items-center space-x-2"
            whileHover={{ scale: 1.1, transition: { duration: 0.2 } }}
          >
            <span className="font-bold text-white">{item.pair}</span>
            <motion.span
              key={`${item.value}-${index}`}
              initial={{ opacity: 0.5, y: 10 }}
              animate={{
                opacity: 1,
                y: 0,
                color: item.increased ? "#4ade80" : "#ef4444",
              }}
              transition={{ duration: 0.3 }}
            >
              {item.value}
            </motion.span>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}

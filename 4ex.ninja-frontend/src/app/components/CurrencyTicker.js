"use client";
import { motion } from "framer-motion";
import { useState, useEffect, useRef } from "react";

const pairs = [
  { pair: "EUR/USD", value: "1.0921" },
  { pair: "GBP/USD", value: "1.2634" },
  { pair: "USD/JPY", value: "148.05" },
  { pair: "USD/CHF", value: "0.8645" },
  { pair: "EUR/GBP", value: "0.8645" },
  { pair: "EUR/JPY", value: "121.45" },
  { pair: "EUR/CHF", value: "1.0634" },
  { pair: "USD/CAD", value: "1.3921" },
  { pair: "AUD/USD", value: "0.6412" },
  { pair: "NZD/USD", value: "0.6012" },
  { pair: "GBP/JPY", value: "187.45" },
  { pair: "GBP/CHF", value: "1.0921" },
  { pair: "AUD/JPY", value: "68.45" },
  { pair: "AUD/NZD", value: "1.0921" },
  { pair: "NZD/JPY", value: "68.45" },
  { pair: "EUR/AUD", value: "1.0921" },
  { pair: "EUR/NZD", value: "1.0921" },
  { pair: "AUD/CHF", value: "1.0921" },
  { pair: "NZD/CHF", value: "1.0921" },
  { pair: "CHF/JPY", value: "1.0921" },
];

export default function CurrencyTicker() {
  const [prices, setPrices] = useState(pairs);
  const containerRef = useRef(null);
  const [containerWidth, setContainerWidth] = useState(0);

  useEffect(() => {
    const updatePrices = () => {
      setPrices((prev) =>
        prev.map((p) => {
          const newValue = (
            Number.parseFloat(p.value) +
            (Math.random() - 0.5) * 0.001
          ).toFixed(4);
          const isIncreased =
            Number.parseFloat(newValue) > Number.parseFloat(p.value);
          return {
            ...p,
            value: newValue,
            increased: isIncreased,
          };
        })
      );
    };

    const interval = setInterval(updatePrices, 2000);

    const updateContainerWidth = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.scrollWidth / 2);
      }
    };

    updateContainerWidth();
    window.addEventListener("resize", updateContainerWidth);

    return () => {
      clearInterval(interval);
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

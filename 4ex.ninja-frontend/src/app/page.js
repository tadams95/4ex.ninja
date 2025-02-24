"use client";
import { motion } from "framer-motion";
import SubscribeButton from "./components/SubscribeButton";
import CurrencyTicker from "./components/CurrencyTicker";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-black text-white">
      <CurrencyTicker />
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="container mx-auto max-w-2xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <motion.h1
              className="text-4xl font-bold mb-6"
              whileHover={{ scale: 1.05 }}
            >
              Welcome to 4ex.ninja
            </motion.h1>
            <motion.p
              className="mb-4 text-lg"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              Get access to premium forex signals and boost your trading
              strategy.
            </motion.p>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
            >
              <SubscribeButton />
            </motion.div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

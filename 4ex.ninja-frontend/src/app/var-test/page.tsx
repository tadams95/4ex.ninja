'use client';

import VaRTrendChart from '../../components/dashboard/VaRTrendChart';

export default function VaRTestPage() {
  return (
    <div className="min-h-screen bg-black p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-8">VaR Trend Chart Test</h1>
        <VaRTrendChart refreshInterval={0} />
      </div>
    </div>
  );
}

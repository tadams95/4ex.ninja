'use client';

import VaRHistoryTest from '../../components/test/VaRHistoryTest';

export default function TestPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">VaR History Hook Test</h1>
        <VaRHistoryTest />
      </div>
    </div>
  );
}

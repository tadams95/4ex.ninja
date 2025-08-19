/**
 * Simplified useRiskData hook for debugging
 */
import { useState } from 'react';

console.log('🔍 [useRiskData-DEBUG] Module loading successfully');

export function useRiskData(refreshInterval: number = 30000) {
  console.log('🔍 [useRiskData-DEBUG] Hook called with interval:', refreshInterval);

  const [varData] = useState(null);
  const [correlationData] = useState(null);
  const [loading] = useState(true);
  const [error] = useState<string | null>(null);
  const [lastUpdate] = useState<Date>(new Date());

  const refetch = () => {
    console.log('🔍 [useRiskData-DEBUG] Refetch called');
  };

  console.log('🔍 [useRiskData-DEBUG] Returning data');

  return {
    varData,
    correlationData,
    loading,
    error,
    lastUpdate,
    refetch,
  };
}

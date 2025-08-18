'use client';

import RiskDashboard from '../../components/dashboard/RiskDashboard';

/**
 * Risk Dashboard Page
 *
 * Route: /risk-dashboard
 * Displays the main risk monitoring dashboard for Phase 2 implementation
 */
export default function RiskDashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto">
        <RiskDashboard />
      </div>
    </div>
  );
}

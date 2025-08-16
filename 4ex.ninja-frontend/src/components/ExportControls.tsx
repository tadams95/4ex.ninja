'use client';

import { useState } from 'react';

interface ExportControlsProps {
  className?: string;
}

export function ExportControls({ className = '' }: ExportControlsProps) {
  const [exporting, setExporting] = useState(false);
  const [exportType, setExportType] = useState<'regime' | 'performance'>('regime');
  const [error, setError] = useState<string | null>(null);

  const handleExport = async (format: 'csv' | 'json') => {
    setExporting(true);
    setError(null);

    try {
      const endpoint =
        exportType === 'regime'
          ? `/export/regime-data?format=${format}`
          : `/export/performance-summary?format=${format}`;

      const response = await fetch(`${process.env.NEXT_PUBLIC_MONITORING_API_URL}${endpoint}`);

      if (!response.ok) {
        throw new Error(`Export failed: ${response.status} ${response.statusText}`);
      }

      if (format === 'csv') {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${exportType}_data_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        const data = await response.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], {
          type: 'application/json',
        });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${exportType}_data_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Export failed:', error);
      setError(error instanceof Error ? error.message : 'Export failed');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className={`flex flex-col space-y-3 ${className}`}>
      {/* Export Type Selection */}
      <div className="flex space-x-2">
        <button
          onClick={() => setExportType('regime')}
          className={`px-3 py-1 text-sm rounded transition-colors ${
            exportType === 'regime'
              ? 'bg-blue-600 text-white'
              : 'bg-neutral-700 text-neutral-300 hover:bg-neutral-600'
          }`}
        >
          Regime Data
        </button>
        <button
          onClick={() => setExportType('performance')}
          className={`px-3 py-1 text-sm rounded transition-colors ${
            exportType === 'performance'
              ? 'bg-blue-600 text-white'
              : 'bg-neutral-700 text-neutral-300 hover:bg-neutral-600'
          }`}
        >
          Performance
        </button>
      </div>

      {/* Export Format Buttons */}
      <div className="flex space-x-2">
        <button
          onClick={() => handleExport('csv')}
          disabled={exporting}
          className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-800 disabled:cursor-not-allowed text-white text-sm rounded-md flex items-center space-x-2 transition-colors"
        >
          {exporting ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <span>📊</span>
          )}
          <span>Export CSV</span>
        </button>

        <button
          onClick={() => handleExport('json')}
          disabled={exporting}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white text-sm rounded-md flex items-center space-x-2 transition-colors"
        >
          {exporting ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <span>📋</span>
          )}
          <span>Export JSON</span>
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="text-red-400 text-sm bg-red-900/20 border border-red-600/30 rounded p-2">
          <div className="flex items-center space-x-2">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Success Message */}
      {!exporting && !error && exportType && (
        <div className="text-neutral-400 text-xs">
          Ready to export {exportType} data in CSV or JSON format
        </div>
      )}
    </div>
  );
}

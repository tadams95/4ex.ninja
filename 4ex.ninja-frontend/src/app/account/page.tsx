'use client';

import ProtectedRoute from '@/components/ProtectedRoute';
import TokenTierDashboard from '@/components/TokenTierDashboard';
import { WalletButton, WalletProfile } from '@/components/WalletConnection';
import { useAuth } from '@/contexts/AuthContext';
import { useTokenBalance } from '@/hooks/useTokenBalanceSimple';
import { TOKEN_CONFIG } from '@/lib/token';
import { Metadata } from 'next';
import Link from 'next/link';
import { useAccount } from 'wagmi';

function AccountPage() {
  const { user, isAuthenticated } = useAuth();
  const { address, isConnected, connector, chain } = useAccount();
  const { balance, tier, isLoading, error, refetch } = useTokenBalance();

  // Check if user is on the correct network
  const isCorrectNetwork = chain?.id === TOKEN_CONFIG.chainId;

  return (
    <div className="min-h-screen bg-black py-12 px-4">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Page Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">Account Dashboard</h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Manage your wallet connection and view your access level
          </p>
        </div>

        {/* Wallet Connection Status */}
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-8">
          <h2 className="text-2xl font-semibold text-white mb-6">Wallet Connection</h2>

          {!isConnected ? (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-gray-700 rounded-full mx-auto mb-4 flex items-center justify-center">
                <svg className="w-8 h-8 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2H4zm0 2h12v8H4V6z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <h3 className="text-xl font-medium text-white mb-2">No Wallet Connected</h3>
              <p className="text-gray-400 mb-6">
                Connect your wallet to access token-gated features
              </p>
              <WalletButton />
            </div>
          ) : (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-medium text-white">Connected Wallet</h3>
                  <p className="text-gray-400">
                    {address ? `${address.slice(0, 8)}...${address.slice(-6)}` : 'Unknown'}
                  </p>
                  {connector && <p className="text-sm text-gray-500">via {connector.name}</p>}
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="text-green-400 text-sm">Connected</span>
                </div>
              </div>

              <WalletProfile />
            </div>
          )}
        </div>

        {/* Token Balance & Access Level */}
        {isConnected && (
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-semibold text-white">Token Access Level</h2>
              {isLoading && (
                <div className="flex items-center space-x-2 text-gray-400">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400"></div>
                  <span className="text-sm">Loading...</span>
                </div>
              )}
            </div>

            {/* Network Check */}
            {!isCorrectNetwork && (
              <div className="bg-yellow-500/20 border border-yellow-500/30 rounded-lg p-6 text-center mb-6">
                <svg
                  className="w-12 h-12 text-yellow-400 mx-auto mb-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                <h3 className="text-lg font-medium text-yellow-400 mb-2">Wrong Network</h3>
                <p className="text-yellow-300 mb-4">
                  Please switch to Base network to view your $4EX token balance
                </p>
                <p className="text-yellow-200 text-sm">
                  Current: {chain?.name || 'Unknown'} (ID: {chain?.id})<br />
                  Required: Base (ID: {TOKEN_CONFIG.chainId})
                </p>
              </div>
            )}

            {error && isCorrectNetwork ? (
              <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-6 text-center">
                <svg
                  className="w-12 h-12 text-red-400 mx-auto mb-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                <h3 className="text-lg font-medium text-red-400 mb-2">
                  Error Loading Token Balance
                </h3>
                <p className="text-red-300 mb-4">{error.message}</p>
                <div className="space-y-2 text-gray-400 text-sm mb-4">
                  <p>Contract: {TOKEN_CONFIG.address}</p>
                  <p>Network: Base (Chain ID: {TOKEN_CONFIG.chainId})</p>
                  <p>Wallet: {address}</p>
                </div>
                <button
                  onClick={() => refetch()}
                  className="px-4 py-2 bg-red-500/30 text-red-300 rounded-md hover:bg-red-500/40 transition-colors"
                >
                  Retry
                </button>
              </div>
            ) : isCorrectNetwork ? (
              <TokenTierDashboard />
            ) : null}
          </div>
        )}

        {/* Debug Information (only show if there's an error or loading) */}
        {isConnected && (isLoading || error || !isCorrectNetwork) && (
          <div className="bg-gray-800 border border-gray-600 rounded-lg p-6">
            <h3 className="text-lg font-medium text-white mb-4">Debug Information</h3>
            <div className="space-y-2 text-sm font-mono">
              <div className="flex justify-between">
                <span className="text-gray-400">Wallet Address:</span>
                <span className="text-white">{address || 'None'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Connected:</span>
                <span className="text-white">{isConnected ? 'Yes' : 'No'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Current Network:</span>
                <span className="text-white">
                  {chain?.name || 'Unknown'} (ID: {chain?.id || 'Unknown'})
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Required Network:</span>
                <span className="text-white">Base (ID: {TOKEN_CONFIG.chainId})</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Network Match:</span>
                <span className={isCorrectNetwork ? 'text-green-400' : 'text-red-400'}>
                  {isCorrectNetwork ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Token Contract:</span>
                <span className="text-white">{TOKEN_CONFIG.address}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Balance Loading:</span>
                <span className="text-white">{isLoading ? 'Yes' : 'No'}</span>
              </div>
              {error && (
                <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded">
                  <div className="text-red-400 text-xs">Error Details:</div>
                  <div className="text-red-300 text-xs mt-1">{error.message}</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="text-center">
          <Link
            href="/feed"
            className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19l-7-7 7-7m8 14l-7-7 7-7"
              />
            </svg>
            Back to Signals Feed
          </Link>
        </div>
      </div>
    </div>
  );
}

// Wrap with ProtectedRoute to ensure wallet is connected
export default function ProtectedAccountPage() {
  return (
    <ProtectedRoute requireWallet={true}>
      <AccountPage />
    </ProtectedRoute>
  );
}

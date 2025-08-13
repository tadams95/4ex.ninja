'use client';

import { WalletButton } from '@/components/WalletConnection';
import { useTokenBalance } from '@/hooks/useTokenBalance';
import { useEffect, useState } from 'react';
import { useAccount } from 'wagmi';

interface MigrationStep {
  id: number;
  title: string;
  description: string;
  completed: boolean;
}

export default function MigrationWizard() {
  const { isConnected, address } = useAccount();
  const { tier } = useTokenBalance();
  const [currentStep, setCurrentStep] = useState(1);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  // Don't show during hydration
  if (!isHydrated) {
    return null;
  }

  const steps: MigrationStep[] = [
    {
      id: 1,
      title: 'Connect Your Wallet',
      description: 'Connect your crypto wallet to access token-gated features',
      completed: isConnected,
    },
    {
      id: 2,
      title: 'Verify Token Balance',
      description: 'Check your $4EX token balance and access tier',
      completed: isConnected && tier !== 'public',
    },
    {
      id: 3,
      title: 'Access Premium Features',
      description: 'Start receiving premium signals based on your tier',
      completed: isConnected && tier !== 'public',
    },
  ];

  const completedSteps = steps.filter(step => step.completed).length;
  const allStepsCompleted = completedSteps === steps.length;

  // Don't show wizard if migration is complete
  if (allStepsCompleted) {
    return null;
  }

  // Find current active step
  useEffect(() => {
    const nextIncompleteStep = steps.find(step => !step.completed);
    if (nextIncompleteStep) {
      setCurrentStep(nextIncompleteStep.id);
    }
  }, [isConnected, tier]);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">Welcome to Token-Gated 4ex.ninja</h2>
        <p className="text-gray-300">
          Complete these steps to access premium features with your $4EX tokens
        </p>
      </div>

      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-400">Progress</span>
          <span className="text-sm text-gray-400">
            {completedSteps}/{steps.length} completed
          </span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div
            className="bg-green-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${(completedSteps / steps.length) * 100}%` }}
          ></div>
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-4">
        {steps.map(step => (
          <div
            key={step.id}
            className={`
              border rounded-lg p-4 transition-all duration-200
              ${
                step.completed
                  ? 'border-green-600 bg-green-900/20'
                  : step.id === currentStep
                  ? 'border-blue-600 bg-blue-900/20'
                  : 'border-gray-700 bg-gray-800/50'
              }
            `}
          >
            <div className="flex items-start space-x-4">
              {/* Step Number/Check */}
              <div
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                  ${
                    step.completed
                      ? 'bg-green-600 text-white'
                      : step.id === currentStep
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300'
                  }
                `}
              >
                {step.completed ? '✓' : step.id}
              </div>

              {/* Step Content */}
              <div className="flex-1">
                <h3 className="text-white font-medium mb-1">{step.title}</h3>
                <p className="text-gray-300 text-sm mb-3">{step.description}</p>

                {/* Step-specific Actions */}
                {step.id === 1 && !isConnected && (
                  <WalletButton variant="primary" size="sm" className="mt-2" />
                )}

                {step.id === 2 && isConnected && tier === 'public' && (
                  <div className="mt-2 p-3 bg-yellow-900/20 border border-yellow-600 rounded">
                    <p className="text-yellow-200 text-sm">
                      No $4EX tokens detected. You'll need to acquire tokens to access premium
                      features.
                    </p>
                    <button className="text-yellow-400 text-sm underline mt-1 hover:text-yellow-300">
                      Learn how to get $4EX →
                    </button>
                  </div>
                )}

                {step.id === 3 && isConnected && tier !== 'public' && (
                  <div className="mt-2 p-3 bg-green-900/20 border border-green-600 rounded">
                    <p className="text-green-200 text-sm">
                      🎉 You're all set! Premium signals are now active for your {tier} tier.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Success Message */}
      {allStepsCompleted && (
        <div className="mt-6 p-4 bg-green-900/20 border border-green-600 rounded-lg">
          <h3 className="text-green-400 font-medium mb-2">Migration Complete! 🎉</h3>
          <p className="text-green-200 text-sm">
            You're now fully migrated to our token-gated system. Enjoy your premium features!
          </p>
        </div>
      )}

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-gray-700">
        <p className="text-gray-400 text-xs text-center">
          Need help? Contact support or check our{' '}
          <a href="/docs" className="text-blue-400 hover:text-blue-300 underline">
            documentation
          </a>
        </p>
      </div>
    </div>
  );
}

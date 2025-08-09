'use client';

import { Button } from '@/components/ui';
import { useRouter } from 'next/navigation';

export default function OfflinePage() {
  const router = useRouter();

  const handleRetry = () => {
    window.location.reload();
  };

  const handleGoHome = () => {
    router.push('/');
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl bg-black min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="mb-6">
          <svg 
            className="mx-auto h-16 w-16 text-gray-400" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={1} 
              d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" 
            />
          </svg>
        </div>
        
        <h1 className="text-3xl font-bold text-white mb-4">You're Offline</h1>
        <p className="text-gray-300 mb-6 max-w-md mx-auto">
          It looks like you've lost your internet connection. Some features may be limited while offline.
        </p>
        
        <div className="space-y-4">
          <div className="bg-gray-800 rounded-lg p-4 text-left">
            <h3 className="font-semibold text-white mb-2">What you can still do:</h3>
            <ul className="text-gray-300 text-sm space-y-1">
              <li>• View previously loaded content</li>
              <li>• Browse cached pages</li>
              <li>• Access your account settings</li>
            </ul>
          </div>
          
          <div className="bg-yellow-500/20 border border-yellow-500/30 rounded-lg p-4 text-left">
            <h3 className="font-semibold text-yellow-400 mb-2">Limited while offline:</h3>
            <ul className="text-yellow-300 text-sm space-y-1">
              <li>• Real-time forex signals</li>
              <li>• Subscription management</li>
              <li>• Account updates</li>
            </ul>
          </div>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-4 mt-8 justify-center">
          <Button onClick={handleRetry} variant="primary">
            Try Again
          </Button>
          <Button onClick={handleGoHome} variant="outline">
            Go Home
          </Button>
        </div>
        
        <p className="text-gray-400 text-sm mt-4">
          Your connection will be restored automatically when you're back online.
        </p>
      </div>
    </div>
  );
}

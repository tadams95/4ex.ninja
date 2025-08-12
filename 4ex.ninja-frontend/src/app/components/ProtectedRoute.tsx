'use client';

import { ProtectedRouteErrorBoundary } from '@/components/error';
import { useAuth } from '@/hooks/api';
import { BaseComponentProps } from '@/types';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

interface ProtectedRouteProps extends BaseComponentProps {
  // Simplified interface - no subscription props needed
}

function ProtectedRouteComponent({ children }: ProtectedRouteProps) {
  const router = useRouter();
  const { isAuthenticated, loading } = useAuth();

  useEffect(() => {
    if (loading) return;
    if (!isAuthenticated) {
      router.push(`/login?callbackUrl=${encodeURIComponent(window.location.href)}`);
    }
  }, [loading, isAuthenticated, router]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen bg-black">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-green-500"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Don't render children until authenticated
    return null;
  }

  return children;
}

export default function ProtectedRoute(props: ProtectedRouteProps) {
  return (
    <ProtectedRouteErrorBoundary>
      <ProtectedRouteComponent {...props} />
    </ProtectedRouteErrorBoundary>
  );
}

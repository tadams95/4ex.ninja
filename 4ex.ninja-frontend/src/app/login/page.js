'use client';

import { AuthErrorBoundary } from '@/components/error';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { logAuthDebug } from '@/lib/auth-debug';
import { signIn } from 'next-auth/react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

function LoginPageComponent() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [detailedError, setDetailedError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const callbackUrl =
    typeof window !== 'undefined'
      ? new URLSearchParams(window.location.search).get('callbackUrl') || '/feed'
      : '/feed';

  const handleSubmit = async e => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setDetailedError('');

    logAuthDebug('environment', {
      nodeEnv: process.env.NODE_ENV,
      apiUrl: process.env.NEXT_PUBLIC_API_URL,
      nextAuthUrl: process.env.NEXTAUTH_URL,
    });

    if (!email || !password) {
      setError('Email and password are required');
      setLoading(false);
      return;
    }

    try {
      logAuthDebug('pre-signin', {
        email,
        hasPassword: !!password,
        callbackUrl,
        env: process.env.NODE_ENV,
      });

      const result = await signIn('credentials', {
        redirect: false,
        email,
        password,
        callbackUrl,
      });

      logAuthDebug('post-signin', {
        ok: result?.ok,
        error: result?.error,
        url: result?.url,
        status: result?.status,
      });

      if (result?.ok && !result.error) {
        router.replace(result.url || callbackUrl);
      } else {
        setError('Invalid email or password');
        setDetailedError(`Auth Error: ${result?.error}. Status: ${result?.status}`);
      }
    } catch (error) {
      logAuthDebug('error', {
        message: error.message,
        stack: process.env.NODE_ENV === 'development' ? error.stack : undefined,
      });
      setError('An unexpected error occurred');
      setDetailedError(error.message);
    } finally {
      setLoading(false);
    }
  };

  // Add debugging information to console on component mount
  useEffect(() => {
    console.log('Login page initialized with callback URL:', callbackUrl);
  }, [callbackUrl]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-black p-4">
      <Card className="max-w-md w-full space-y-8" padding="lg">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-white">
            Sign in to your account
          </h2>
        </div>

        {error && (
          <div className="bg-error/20 text-error p-3 rounded-md">
            <p className="font-medium">{error}</p>
            {detailedError && <p className="text-sm mt-1 text-error/80">{detailedError}</p>}
          </div>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <Input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              placeholder="Email address"
              value={email}
              onChange={e => setEmail(e.target.value)}
            />

            <Input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              placeholder="Password"
              value={password}
              onChange={e => setPassword(e.target.value)}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="text-sm">
              <Link
                href="/forgot-password"
                className="font-medium text-primary-500 hover:text-primary-400"
              >
                Forgot your password?
              </Link>
            </div>
          </div>

          <Button type="submit" disabled={loading} className="w-full" loading={loading}>
            Sign in
          </Button>
        </form>

        <div className="text-center text-sm">
          <span className="text-neutral-400">Don't have an account?</span>{' '}
          <Link href="/register" className="font-medium text-primary-500 hover:text-primary-400">
            Register
          </Link>
        </div>
      </Card>
    </div>
  );
}

// Wrap the component with AuthErrorBoundary
export default function LoginPage() {
  return (
    <AuthErrorBoundary>
      <LoginPageComponent />
    </AuthErrorBoundary>
  );
}

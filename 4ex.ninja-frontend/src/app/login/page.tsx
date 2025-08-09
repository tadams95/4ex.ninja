'use client';

import { AuthErrorBoundary } from '@/components/error';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { logAuthDebug } from '@/lib/auth-debug';
import {
  formatRemainingTime,
  loginRateLimit,
  loginSchema,
  sanitizeTextInput,
} from '@/lib/security';
import { signIn } from 'next-auth/react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { z } from 'zod';

function LoginPageComponent() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState('');
  const [detailedError, setDetailedError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const callbackUrl =
    typeof window !== 'undefined'
      ? new URLSearchParams(window.location.search).get('callbackUrl') || '/feed'
      : '/feed';

  const handleInputChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = field === 'email' ? sanitizeTextInput(e.target.value) : e.target.value;
    setFormData(prev => ({ ...prev, [field]: value }));

    // Clear field-specific error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const validateForm = (): boolean => {
    try {
      loginSchema.parse(formData);
      setErrors({});
      return true;
    } catch (error) {
      if (error instanceof z.ZodError) {
        const newErrors: Record<string, string> = {};
        error.issues.forEach(issue => {
          if (issue.path[0]) {
            newErrors[issue.path[0] as string] = issue.message;
          }
        });
        setErrors(newErrors);
      }
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setGeneralError('');
    setDetailedError('');

    logAuthDebug('environment', {
      nodeEnv: process.env.NODE_ENV,
      apiUrl: process.env.NEXT_PUBLIC_API_URL,
      nextAuthUrl: process.env.NEXTAUTH_URL,
    });

    // Rate limiting check
    const clientId = `login_${formData.email}`;
    if (!loginRateLimit.canAttempt(clientId)) {
      const remainingTime = loginRateLimit.getRemainingTime(clientId);
      setGeneralError(
        `Too many login attempts. Please try again in ${formatRemainingTime(remainingTime)}.`
      );
      setLoading(false);
      return;
    }

    // Client-side validation
    if (!validateForm()) {
      setLoading(false);
      return;
    }

    try {
      logAuthDebug('pre-signin', {
        email: formData.email,
        hasPassword: !!formData.password,
        callbackUrl,
        env: process.env.NODE_ENV,
      });

      const result = await signIn('credentials', {
        redirect: false,
        email: formData.email,
        password: formData.password,
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
        setGeneralError('Invalid email or password');
        setDetailedError(`Auth Error: ${result?.error}. Status: ${result?.status}`);
      }
    } catch (error) {
      logAuthDebug('error', {
        message: (error as Error).message,
        stack: process.env.NODE_ENV === 'development' ? (error as Error).stack : undefined,
      });
      setGeneralError('An unexpected error occurred');
      setDetailedError((error as Error).message);
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

        {generalError && (
          <div className="bg-error/20 text-error p-3 rounded-md">
            <p className="font-medium">{generalError}</p>
            {detailedError && <p className="text-sm mt-1 text-error/80">{detailedError}</p>}
          </div>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleSubmit} data-testid="login-form">
          <div className="space-y-4">
            <div>
              <Input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                placeholder="Email address"
                value={formData.email}
                onChange={handleInputChange('email')}
                className={errors.email ? 'border-red-500' : ''}
                data-testid="email-input"
              />
              {errors.email && <p className="text-red-400 text-sm mt-1">{errors.email}</p>}
            </div>

            <div>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                placeholder="Password"
                value={formData.password}
                onChange={handleInputChange('password')}
                className={errors.password ? 'border-red-500' : ''}
                data-testid="password-input"
              />
              {errors.password && <p className="text-red-400 text-sm mt-1">{errors.password}</p>}
            </div>
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

          <Button
            type="submit"
            disabled={loading}
            className="w-full"
            loading={loading}
            data-testid="login-button"
          >
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

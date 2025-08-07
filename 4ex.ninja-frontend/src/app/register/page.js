'use client';

import { AuthErrorBoundary } from '@/components/error';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { handleCheckout } from '@/utils/checkout-helpers';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

function RegisterPageComponent() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const router = useRouter();

  const handleSubmit = async e => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Client-side validation
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Registration failed');
      }

      // Show success message
      setSuccess(true);

      // Proceed to checkout instead of redirecting to login
      setTimeout(() => {
        handleCheckout().catch(err => {
          console.error('Checkout error after registration:', err);
          // Fallback to login page if checkout fails
          router.push('/login');
        });
      }, 2000);
    } catch (err) {
      console.error('Registration error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-black p-4">
      <Card className="max-w-md w-full space-y-8" padding="lg">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-white">
            Create your account
          </h2>
        </div>

        {error && <div className="bg-error/20 text-error p-3 rounded-md text-center">{error}</div>}

        {success && (
          <div className="bg-success/20 text-success p-3 rounded-md text-center">
            Account created successfully! Redirecting to checkout...
          </div>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleSubmit} data-testid="register-form">
          <div className="space-y-4">
            <Input
              id="name"
              name="name"
              type="text"
              autoComplete="name"
              required
              placeholder="Full Name"
              value={name}
              onChange={e => setName(e.target.value)}
              data-testid="first-name-input"
            />

            <Input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              placeholder="Email address"
              value={email}
              onChange={e => setEmail(e.target.value)}
              data-testid="email-input"
            />

            <Input
              id="password"
              name="password"
              type="password"
              autoComplete="new-password"
              required
              placeholder="Password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              data-testid="password-input"
            />

            <Input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              autoComplete="new-password"
              required
              placeholder="Confirm Password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              data-testid="confirm-password-input"
            />
          </div>

          <Button
            type="submit"
            disabled={loading || success}
            className="w-full"
            loading={loading}
            data-testid="register-button"
          >
            {success ? 'Account Created!' : 'Create Account'}
          </Button>
        </form>

        <div className="text-center text-sm">
          <span className="text-neutral-400">Already have an account?</span>{' '}
          <Link href="/login" className="font-medium text-primary-500 hover:text-primary-400">
            Sign in
          </Link>
        </div>
      </Card>
    </div>
  );
}

// Wrap the component with AuthErrorBoundary
export default function RegisterPage() {
  return (
    <AuthErrorBoundary>
      <RegisterPageComponent />
    </AuthErrorBoundary>
  );
}

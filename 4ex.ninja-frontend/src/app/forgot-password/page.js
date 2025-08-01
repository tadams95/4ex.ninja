'use client';

import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import Link from 'next/link';
import { useState } from 'react';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async e => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess(false);

    if (!email) {
      setError('Email is required');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to process request');
      }

      setSuccess(true);
    } catch (err) {
      console.error('Forgot password error:', err);
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
            Reset Your Password
          </h2>
          <p className="mt-2 text-center text-sm text-neutral-400">
            Enter your email address and we'll send you a link to reset your password.
          </p>
        </div>

        {error && <div className="bg-error/20 text-error p-3 rounded-md text-center">{error}</div>}

        {success ? (
          <div className="space-y-6">
            <div className="bg-success/20 text-success p-4 rounded-md text-center">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-12 w-12 mx-auto mb-3"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
              <h3 className="text-lg font-semibold mb-2">Check your inbox</h3>
              <p className="text-sm">
                If an account exists with the email <strong>{email}</strong>, we've sent password
                reset instructions.
              </p>
            </div>
            <div className="text-center">
              <Link href="/login" className="font-medium text-primary-500 hover:text-primary-400">
                Return to login
              </Link>
            </div>
          </div>
        ) : (
          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
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

            <Button type="submit" disabled={loading} className="w-full" loading={loading}>
              Send Reset Link
            </Button>

            <div className="text-center text-sm">
              <Link href="/login" className="font-medium text-primary-500 hover:text-primary-400">
                Back to sign in
              </Link>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
}

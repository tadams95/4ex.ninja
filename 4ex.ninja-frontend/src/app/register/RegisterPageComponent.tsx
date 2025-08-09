'use client';

import { AuthErrorBoundary } from '@/components/error';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import {
  formatRemainingTime,
  getSecureHeaders,
  registerRateLimit,
  registrationSchema,
  sanitizeTextInput,
} from '@/lib/security';
import { handleCheckout } from '@/utils/checkout-helpers';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { z } from 'zod';

function RegisterPageComponent() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const router = useRouter();

  const handleInputChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = sanitizeTextInput(e.target.value);
    setFormData(prev => ({ ...prev, [field]: value }));

    // Clear field-specific error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const validateForm = (): boolean => {
    try {
      registrationSchema.parse(formData);
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

    // Rate limiting check
    const clientId = `register_${formData.email}`;
    if (!registerRateLimit.canAttempt(clientId)) {
      const remainingTime = registerRateLimit.getRemainingTime(clientId);
      setGeneralError(
        `Too many registration attempts. Please try again in ${formatRemainingTime(remainingTime)}.`
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
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: getSecureHeaders(),
        body: JSON.stringify({
          name: formData.name,
          email: formData.email,
          password: formData.password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Registration failed');
      }

      setSuccess(true);
      // Auto-redirect to subscription checkout
      setTimeout(() => {
        handleCheckout();
      }, 2000);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Registration failed';
      setGeneralError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center p-4">
        <div className="max-w-md w-full">
          <Card className="p-8 text-center bg-gray-800 border-gray-700">
            <div className="text-green-400 text-5xl mb-4">✓</div>
            <h1 className="text-2xl font-bold mb-4">Registration Successful!</h1>
            <p className="text-gray-300 mb-6">
              Your account has been created successfully. Redirecting you to checkout...
            </p>
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-green-400"></div>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <Card className="p-8 bg-gray-800 border-gray-700">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold mb-2">Create Your Account</h1>
            <p className="text-gray-400">
              Join 4ex.ninja and start receiving premium forex signals
            </p>
          </div>

          {generalError && (
            <div className="mb-6 p-4 bg-red-900/20 border border-red-800 rounded-md">
              <p className="text-red-400 text-sm">{generalError}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-2">
                Full Name
              </label>
              <Input
                type="text"
                id="name"
                value={formData.name}
                onChange={handleInputChange('name')}
                className={`w-full bg-gray-700 border-gray-600 text-white ${
                  errors.name ? 'border-red-500' : ''
                }`}
                placeholder="Enter your full name"
                required
              />
              {errors.name && <p className="text-red-400 text-sm mt-1">{errors.name}</p>}
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                Email Address
              </label>
              <Input
                type="email"
                id="email"
                value={formData.email}
                onChange={handleInputChange('email')}
                className={`w-full bg-gray-700 border-gray-600 text-white ${
                  errors.email ? 'border-red-500' : ''
                }`}
                placeholder="Enter your email"
                required
              />
              {errors.email && <p className="text-red-400 text-sm mt-1">{errors.email}</p>}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
                Password
              </label>
              <Input
                type="password"
                id="password"
                value={formData.password}
                onChange={handleInputChange('password')}
                className={`w-full bg-gray-700 border-gray-600 text-white ${
                  errors.password ? 'border-red-500' : ''
                }`}
                placeholder="Create a strong password"
                required
              />
              {errors.password && <p className="text-red-400 text-sm mt-1">{errors.password}</p>}
              <p className="text-gray-400 text-xs mt-1">
                Must contain uppercase, lowercase, number, and special character
              </p>
            </div>

            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium text-gray-300 mb-2"
              >
                Confirm Password
              </label>
              <Input
                type="password"
                id="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleInputChange('confirmPassword')}
                className={`w-full bg-gray-700 border-gray-600 text-white ${
                  errors.confirmPassword ? 'border-red-500' : ''
                }`}
                placeholder="Confirm your password"
                required
              />
              {errors.confirmPassword && (
                <p className="text-red-400 text-sm mt-1">{errors.confirmPassword}</p>
              )}
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-green-600 hover:bg-green-700 disabled:bg-green-800"
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Creating Account...
                </div>
              ) : (
                'Create Account & Subscribe'
              )}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-400 text-sm">
              Already have an account?{' '}
              <Link href="/login" className="text-green-400 hover:text-green-300">
                Sign in here
              </Link>
            </p>
          </div>

          <div className="mt-4 text-center">
            <p className="text-xs text-gray-500">
              By creating an account, you agree to our{' '}
              <Link href="/terms" className="text-green-400 hover:text-green-300">
                Terms of Service
              </Link>{' '}
              and{' '}
              <Link href="/privacy" className="text-green-400 hover:text-green-300">
                Privacy Policy
              </Link>
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}

export default function RegisterPageWithBoundary() {
  return (
    <AuthErrorBoundary>
      <RegisterPageComponent />
    </AuthErrorBoundary>
  );
}

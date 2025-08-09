/**
 * Custom hooks for security and form validation
 */

import { sanitizeTextInput } from '@/lib/security';
import { useCallback, useState } from 'react';
import { z } from 'zod';

interface UseSecureFormOptions<T> {
  schema: z.ZodSchema<T>;
  onSubmit: (data: T) => Promise<void> | void;
  sanitizeFields?: (keyof T)[];
}

interface UseSecureFormReturn<T> {
  formData: Partial<T>;
  errors: Record<string, string>;
  isSubmitting: boolean;
  handleInputChange: (field: keyof T) => (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleSubmit: (e: React.FormEvent) => Promise<void>;
  setFieldError: (field: keyof T, error: string) => void;
  clearErrors: () => void;
}

/**
 * Secure form hook with built-in validation and sanitization
 */
export function useSecureForm<T>({
  schema,
  onSubmit,
  sanitizeFields = [],
}: UseSecureFormOptions<T>): UseSecureFormReturn<T> {
  const [formData, setFormData] = useState<Partial<T>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleInputChange = useCallback(
    (field: keyof T) => (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = sanitizeFields.includes(field)
        ? sanitizeTextInput(e.target.value)
        : e.target.value;

      setFormData(prev => ({ ...prev, [field]: value }));

      // Clear field-specific error when user starts typing
      if (errors[field as string]) {
        setErrors(prev => ({ ...prev, [field as string]: '' }));
      }
    },
    [sanitizeFields, errors]
  );

  const validateForm = useCallback((): boolean => {
    try {
      schema.parse(formData);
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
  }, [formData, schema]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!validateForm()) {
        return;
      }

      setIsSubmitting(true);
      try {
        await onSubmit(formData as T);
      } finally {
        setIsSubmitting(false);
      }
    },
    [formData, validateForm, onSubmit]
  );

  const setFieldError = useCallback((field: keyof T, error: string) => {
    setErrors(prev => ({ ...prev, [field as string]: error }));
  }, []);

  const clearErrors = useCallback(() => {
    setErrors({});
  }, []);

  return {
    formData,
    errors,
    isSubmitting,
    handleInputChange,
    handleSubmit,
    setFieldError,
    clearErrors,
  };
}

/**
 * Hook for managing rate limiting on the client side
 */
export function useRateLimit(maxAttempts: number = 5, windowMs: number = 15 * 60 * 1000) {
  const [isBlocked, setIsBlocked] = useState(false);
  const [remainingTime, setRemainingTime] = useState(0);

  const checkRateLimit = useCallback(
    (key: string): boolean => {
      const storageKey = `rate_limit_${key}`;
      const now = Date.now();

      try {
        const stored = localStorage.getItem(storageKey);
        const attempts = stored ? JSON.parse(stored) : [];

        // Remove old attempts outside the window
        const validAttempts = attempts.filter((time: number) => now - time < windowMs);

        if (validAttempts.length >= maxAttempts) {
          const oldestAttempt = Math.min(...validAttempts);
          const remaining = windowMs - (now - oldestAttempt);
          setIsBlocked(true);
          setRemainingTime(remaining);
          return false;
        }

        // Add current attempt
        validAttempts.push(now);
        localStorage.setItem(storageKey, JSON.stringify(validAttempts));

        setIsBlocked(false);
        setRemainingTime(0);
        return true;
      } catch (error) {
        // Fallback if localStorage is not available
        console.warn('Rate limiting storage not available:', error);
        return true;
      }
    },
    [maxAttempts, windowMs]
  );

  return { isBlocked, remainingTime, checkRateLimit };
}

/**
 * Hook for secure password validation with real-time feedback
 */
export function usePasswordValidation() {
  const [strength, setStrength] = useState<'weak' | 'medium' | 'strong'>('weak');
  const [criteria, setCriteria] = useState({
    minLength: false,
    hasUppercase: false,
    hasLowercase: false,
    hasNumber: false,
    hasSpecialChar: false,
  });

  const validatePassword = useCallback((password: string) => {
    const newCriteria = {
      minLength: password.length >= 8,
      hasUppercase: /[A-Z]/.test(password),
      hasLowercase: /[a-z]/.test(password),
      hasNumber: /[0-9]/.test(password),
      hasSpecialChar: /[^A-Za-z0-9]/.test(password),
    };

    setCriteria(newCriteria);

    const score = Object.values(newCriteria).filter(Boolean).length;
    if (score < 3) {
      setStrength('weak');
    } else if (score < 5) {
      setStrength('medium');
    } else {
      setStrength('strong');
    }

    return newCriteria;
  }, []);

  return { strength, criteria, validatePassword };
}

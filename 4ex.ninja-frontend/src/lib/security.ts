/**
 * Security utilities for input validation and sanitization
 */

import DOMPurify from 'dompurify';
import { z } from 'zod';

// Email validation schema
export const emailSchema = z
  .string()
  .email('Please enter a valid email address')
  .min(3, 'Email must be at least 3 characters')
  .max(255, 'Email must be less than 255 characters')
  .transform(email => email.toLowerCase().trim());

// Password validation schema
export const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .max(128, 'Password must be less than 128 characters')
  .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
  .regex(/[0-9]/, 'Password must contain at least one number')
  .regex(/[^A-Za-z0-9]/, 'Password must contain at least one special character');

// Name validation schema
export const nameSchema = z
  .string()
  .min(2, 'Name must be at least 2 characters')
  .max(50, 'Name must be less than 50 characters')
  .regex(/^[a-zA-Z\s'-]+$/, 'Name can only contain letters, spaces, hyphens, and apostrophes')
  .transform(name => name.trim());

// Registration form validation schema
export const registrationSchema = z
  .object({
    name: nameSchema,
    email: emailSchema,
    password: passwordSchema,
    confirmPassword: z.string(),
  })
  .refine(data => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

// Login form validation schema
export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, 'Password is required'),
});

// HTML sanitization function
export const sanitizeHtml = (dirty: string): string => {
  if (typeof window === 'undefined') {
    // Server-side: return empty string or implement server-side sanitization
    return '';
  }

  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: [], // Remove all HTML tags
    ALLOWED_ATTR: [], // Remove all attributes
    KEEP_CONTENT: true, // Keep text content
  });
};

// Safe text input sanitization (removes HTML but keeps text)
export const sanitizeTextInput = (input: string): string => {
  if (!input || typeof input !== 'string') return '';

  // Remove HTML tags and decode entities, then trim
  const sanitized = sanitizeHtml(input);
  return sanitized.trim();
};

// Rate limiting helper for client-side
export class ClientRateLimit {
  private attempts: Map<string, number[]> = new Map();
  private readonly maxAttempts: number;
  private readonly windowMs: number;

  constructor(maxAttempts: number = 5, windowMs: number = 15 * 60 * 1000) {
    // 15 minutes
    this.maxAttempts = maxAttempts;
    this.windowMs = windowMs;
  }

  canAttempt(key: string): boolean {
    const now = Date.now();
    const attempts = this.attempts.get(key) || [];

    // Remove old attempts outside the window
    const validAttempts = attempts.filter(time => now - time < this.windowMs);

    if (validAttempts.length >= this.maxAttempts) {
      return false;
    }

    // Add current attempt
    validAttempts.push(now);
    this.attempts.set(key, validAttempts);

    return true;
  }

  getRemainingTime(key: string): number {
    const attempts = this.attempts.get(key) || [];
    if (attempts.length < this.maxAttempts) return 0;

    const oldestAttempt = Math.min(...attempts);
    const remainingTime = this.windowMs - (Date.now() - oldestAttempt);

    return Math.max(0, remainingTime);
  }
}

// Create rate limiter instances
export const loginRateLimit = new ClientRateLimit(5, 15 * 60 * 1000); // 5 attempts per 15 minutes
export const registerRateLimit = new ClientRateLimit(3, 30 * 60 * 1000); // 3 attempts per 30 minutes

// Utility to format remaining time
export const formatRemainingTime = (ms: number): string => {
  const minutes = Math.ceil(ms / (60 * 1000));
  return `${minutes} minute${minutes !== 1 ? 's' : ''}`;
};

// CSRF token validation (for forms)
export const generateCSRFToken = (): string => {
  if (typeof window === 'undefined') return '';

  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
};

// Secure headers for API requests
export const getSecureHeaders = (csrfToken?: string): HeadersInit => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
  };

  if (csrfToken) {
    headers['X-CSRF-Token'] = csrfToken;
  }

  return headers;
};

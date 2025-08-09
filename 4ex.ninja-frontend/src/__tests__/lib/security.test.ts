/**
 * @jest-environment jsdom
 */

import {
  ClientRateLimit,
  emailSchema,
  generateCSRFToken,
  getSecureHeaders,
  loginSchema,
  nameSchema,
  passwordSchema,
  registrationSchema,
  sanitizeTextInput,
} from '@/lib/security';
import { beforeEach, describe, expect, it, jest } from '@jest/globals';

// Mock DOMPurify for testing
jest.mock('dompurify', () => ({
  sanitize: jest.fn((dirty: string) => dirty.replace(/<[^>]*>/g, '')),
}));

describe('Security Utilities', () => {
  describe('Email Schema Validation', () => {
    it('should validate correct email addresses', () => {
      expect(emailSchema.parse('test@example.com')).toBe('test@example.com');
      expect(emailSchema.parse('user.name@domain.co.uk')).toBe('user.name@domain.co.uk');
    });

    it('should transform email to lowercase and trim', () => {
      expect(emailSchema.parse('TEST@EXAMPLE.COM')).toBe('test@example.com');
    });

    it('should reject invalid email addresses', () => {
      expect(() => emailSchema.parse('invalid-email')).toThrow();
      expect(() => emailSchema.parse('test@')).toThrow();
      expect(() => emailSchema.parse('@example.com')).toThrow();
    });
  });

  describe('Password Schema Validation', () => {
    it('should validate strong passwords', () => {
      const strongPassword = 'MyStr0ng!Pass';
      expect(passwordSchema.parse(strongPassword)).toBe(strongPassword);
    });

    it('should reject weak passwords', () => {
      expect(() => passwordSchema.parse('weak')).toThrow('Password must be at least 8 characters');
      expect(() => passwordSchema.parse('password123')).toThrow(
        'Password must contain at least one uppercase letter'
      );
      expect(() => passwordSchema.parse('PASSWORD123!')).toThrow(
        'Password must contain at least one lowercase letter'
      );
      expect(() => passwordSchema.parse('Password!')).toThrow(
        'Password must contain at least one number'
      );
      expect(() => passwordSchema.parse('Password123')).toThrow(
        'Password must contain at least one special character'
      );
    });
  });

  describe('Name Schema Validation', () => {
    it('should validate correct names', () => {
      expect(nameSchema.parse('John Doe')).toBe('John Doe');
      expect(nameSchema.parse("O'Connor")).toBe("O'Connor");
      expect(nameSchema.parse('Mary-Jane')).toBe('Mary-Jane');
    });

    it('should trim whitespace', () => {
      expect(nameSchema.parse('  John Doe  ')).toBe('John Doe');
    });

    it('should reject invalid names', () => {
      expect(() => nameSchema.parse('A')).toThrow('Name must be at least 2 characters');
      expect(() => nameSchema.parse('John123')).toThrow('Name can only contain letters');
      expect(() => nameSchema.parse('John@Doe')).toThrow('Name can only contain letters');
    });
  });

  describe('Registration Schema Validation', () => {
    const validRegistration = {
      name: 'John Doe',
      email: 'john@example.com',
      password: 'MyStr0ng!Pass',
      confirmPassword: 'MyStr0ng!Pass',
    };

    it('should validate correct registration data', () => {
      expect(registrationSchema.parse(validRegistration)).toEqual({
        name: 'John Doe',
        email: 'john@example.com',
        password: 'MyStr0ng!Pass',
        confirmPassword: 'MyStr0ng!Pass',
      });
    });

    it('should reject when passwords do not match', () => {
      const invalidData = {
        ...validRegistration,
        confirmPassword: 'DifferentPassword!',
      };
      expect(() => registrationSchema.parse(invalidData)).toThrow();
    });
  });

  describe('Login Schema Validation', () => {
    it('should validate correct login data', () => {
      const loginData = {
        email: 'test@example.com',
        password: 'password123',
      };
      expect(loginSchema.parse(loginData)).toEqual({
        email: 'test@example.com',
        password: 'password123',
      });
    });

    it('should reject empty password', () => {
      const invalidData = {
        email: 'test@example.com',
        password: '',
      };
      expect(() => loginSchema.parse(invalidData)).toThrow('Password is required');
    });
  });

  describe('HTML Sanitization', () => {
    it('should sanitize HTML input', () => {
      // Mock window for this test
      const originalWindow = global.window;
      global.window = {} as any;

      const dirtyHtml = '<script>alert("xss")</script>Hello World';
      const sanitized = sanitizeTextInput(dirtyHtml);
      expect(sanitized).toBe('Hello World');

      // Restore window
      global.window = originalWindow;
    });

    it('should handle empty or null input', () => {
      expect(sanitizeTextInput('')).toBe('');
      expect(sanitizeTextInput(null as any)).toBe('');
      expect(sanitizeTextInput(undefined as any)).toBe('');
    });
  });

  describe('Client Rate Limiting', () => {
    let rateLimit: ClientRateLimit;

    beforeEach(() => {
      rateLimit = new ClientRateLimit(3, 1000); // 3 attempts per second for testing
    });

    it('should allow requests within limit', () => {
      expect(rateLimit.canAttempt('test-key')).toBe(true);
      expect(rateLimit.canAttempt('test-key')).toBe(true);
      expect(rateLimit.canAttempt('test-key')).toBe(true);
    });

    it('should block requests after limit is exceeded', () => {
      // Exhaust the limit
      rateLimit.canAttempt('test-key');
      rateLimit.canAttempt('test-key');
      rateLimit.canAttempt('test-key');

      // Should now be blocked
      expect(rateLimit.canAttempt('test-key')).toBe(false);
    });

    it('should calculate remaining time correctly', () => {
      // Exhaust the limit
      rateLimit.canAttempt('test-key');
      rateLimit.canAttempt('test-key');
      rateLimit.canAttempt('test-key');

      const remainingTime = rateLimit.getRemainingTime('test-key');
      expect(remainingTime).toBeGreaterThan(0);
      expect(remainingTime).toBeLessThanOrEqual(1000);
    });
  });

  describe('CSRF Token Generation', () => {
    beforeEach(() => {
      // Mock crypto.getRandomValues
      Object.defineProperty(global, 'crypto', {
        value: {
          getRandomValues: jest.fn((array: Uint8Array) => {
            for (let i = 0; i < array.length; i++) {
              array[i] = Math.floor(Math.random() * 256);
            }
            return array;
          }),
        },
      });
    });

    it('should generate a token', () => {
      const token = generateCSRFToken();
      expect(typeof token).toBe('string');
      expect(token.length).toBe(64); // 32 bytes * 2 hex chars
    });

    it('should generate different tokens on each call', () => {
      const token1 = generateCSRFToken();
      const token2 = generateCSRFToken();
      expect(token1).not.toBe(token2);
    });
  });

  describe('Secure Headers', () => {
    it('should generate basic secure headers', () => {
      const headers = getSecureHeaders();
      expect(headers).toEqual({
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
      });
    });

    it('should include CSRF token when provided', () => {
      const csrfToken = 'test-csrf-token';
      const headers = getSecureHeaders(csrfToken);
      expect(headers).toEqual({
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRF-Token': csrfToken,
      });
    });
  });
});

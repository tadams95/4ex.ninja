/**
 * Comprehensive API error handling utility for 4ex.ninja
 * Provides consistent error handling, retry logic, and error classification
 */

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: unknown;
  timestamp: string;
  endpoint?: string;
}

export interface RetryConfig {
  maxRetries: number;
  baseDelay: number; // ms
  maxDelay: number; // ms
  retryCondition?: (error: ApiError) => boolean;
}

export interface ErrorLogEntry {
  error: ApiError;
  userAgent: string;
  url: string;
  userId?: string;
  sessionId?: string;
}

export class ApiErrorHandler {
  private static instance: ApiErrorHandler;
  private retryConfig: RetryConfig = {
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: 10000,
    retryCondition: error => this.isRetryableError(error),
  };

  static getInstance(): ApiErrorHandler {
    if (!ApiErrorHandler.instance) {
      ApiErrorHandler.instance = new ApiErrorHandler();
    }
    return ApiErrorHandler.instance;
  }

  /**
   * Handle API response and convert errors to standardized format
   */
  async handleResponse<T>(response: Response, endpoint?: string): Promise<T> {
    if (!response.ok) {
      const error = await this.createApiError(response, endpoint);
      this.logError(error);
      throw error;
    }

    try {
      return await response.json();
    } catch (parseError) {
      const error: ApiError = {
        message: 'Failed to parse response JSON',
        status: response.status,
        code: 'PARSE_ERROR',
        details: parseError,
        timestamp: new Date().toISOString(),
        endpoint,
      };
      this.logError(error);
      throw error;
    }
  }

  /**
   * Execute API call with automatic retry logic
   */
  async withRetry<T>(apiCall: () => Promise<T>, config?: Partial<RetryConfig>): Promise<T> {
    const finalConfig = { ...this.retryConfig, ...config };
    let lastError: ApiError;

    for (let attempt = 0; attempt <= finalConfig.maxRetries; attempt++) {
      try {
        return await apiCall();
      } catch (error) {
        lastError = this.normalizeError(error);

        // Don't retry on final attempt or non-retryable errors
        if (attempt === finalConfig.maxRetries || !finalConfig.retryCondition!(lastError)) {
          break;
        }

        // Calculate delay with exponential backoff
        const delay = Math.min(finalConfig.baseDelay * Math.pow(2, attempt), finalConfig.maxDelay);

        await this.delay(delay);
      }
    }

    throw lastError!;
  }

  /**
   * Check if error is retryable (network errors, 5xx status codes)
   */
  private isRetryableError(error: ApiError): boolean {
    // Network errors (no status)
    if (!error.status) return true;

    // Server errors (5xx)
    if (error.status >= 500) return true;

    // Rate limiting (429)
    if (error.status === 429) return true;

    // Timeout errors
    if (error.code === 'TIMEOUT') return true;

    return false;
  }

  /**
   * Check if error indicates offline status
   */
  isOfflineError(error: ApiError): boolean {
    return (
      !error.status ||
      error.code === 'NETWORK_ERROR' ||
      error.message.toLowerCase().includes('network') ||
      error.message.toLowerCase().includes('offline')
    );
  }

  /**
   * Get user-friendly error message
   */
  getUserFriendlyMessage(error: ApiError): string {
    if (this.isOfflineError(error)) {
      return 'You appear to be offline. Please check your internet connection.';
    }

    switch (error.status) {
      case 401:
        return 'Your session has expired. Please log in again.';
      case 403:
        return 'You do not have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 429:
        return 'Too many requests. Please try again in a moment.';
      case 500:
      case 502:
      case 503:
      case 504:
        return 'Our servers are experiencing issues. Please try again later.';
      default:
        return error.message || 'An unexpected error occurred. Please try again.';
    }
  }

  /**
   * Create standardized API error from response
   */
  private async createApiError(response: Response, endpoint?: string): Promise<ApiError> {
    let message = `HTTP ${response.status}: ${response.statusText}`;
    let details: unknown;

    try {
      const responseData = await response.json();
      message = responseData.message || responseData.error || message;
      details = responseData;
    } catch {
      // Ignore JSON parse errors for error responses
    }

    return {
      message,
      status: response.status,
      code: this.getErrorCode(response.status),
      details,
      timestamp: new Date().toISOString(),
      endpoint,
    };
  }

  /**
   * Normalize any error to ApiError format
   */
  private normalizeError(error: unknown): ApiError {
    if (this.isApiError(error)) {
      return error;
    }

    if (error instanceof Error) {
      return {
        message: error.message,
        code: error.name === 'TypeError' ? 'NETWORK_ERROR' : 'UNKNOWN_ERROR',
        details: error,
        timestamp: new Date().toISOString(),
      };
    }

    return {
      message: 'An unknown error occurred',
      code: 'UNKNOWN_ERROR',
      details: error,
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Type guard for ApiError
   */
  private isApiError(error: unknown): error is ApiError {
    return (
      typeof error === 'object' && error !== null && 'message' in error && 'timestamp' in error
    );
  }

  /**
   * Get error code from HTTP status
   */
  private getErrorCode(status: number): string {
    if (status >= 500) return 'SERVER_ERROR';
    if (status === 429) return 'RATE_LIMITED';
    if (status === 404) return 'NOT_FOUND';
    if (status === 403) return 'FORBIDDEN';
    if (status === 401) return 'UNAUTHORIZED';
    if (status >= 400) return 'CLIENT_ERROR';
    return 'UNKNOWN_ERROR';
  }

  /**
   * Log error for monitoring and debugging
   */
  private logError(error: ApiError): void {
    const logEntry: ErrorLogEntry = {
      error,
      userAgent: navigator.userAgent,
      url: window.location.href,
      // Add user/session context if available
      userId: this.getCurrentUserId(),
      sessionId: this.getSessionId(),
    };

    // Console logging for development
    if (process.env.NODE_ENV === 'development') {
      console.error('API Error:', logEntry);
    }

    // TODO: Send to error tracking service (Sentry, etc.)
    // This would be implemented when error monitoring is added
    this.sendToErrorService(logEntry);
  }

  /**
   * Get current user ID from session/auth context
   */
  private getCurrentUserId(): string | undefined {
    // This would integrate with your auth system
    // For now, return undefined
    return undefined;
  }

  /**
   * Get session ID for correlation
   */
  private getSessionId(): string | undefined {
    // Generate or retrieve session ID
    let sessionId = sessionStorage.getItem('errorSessionId');
    if (!sessionId) {
      sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      sessionStorage.setItem('errorSessionId', sessionId);
    }
    return sessionId;
  }

  /**
   * Send error to monitoring service (placeholder for future implementation)
   */
  private sendToErrorService(logEntry: ErrorLogEntry): void {
    // Placeholder for error monitoring service integration
    // Could integrate with Sentry, LogRocket, etc.

    // For now, just store in localStorage for debugging
    try {
      const errors = JSON.parse(localStorage.getItem('apiErrors') || '[]');
      errors.push(logEntry);
      // Keep only last 50 errors
      if (errors.length > 50) {
        errors.splice(0, errors.length - 50);
      }
      localStorage.setItem('apiErrors', JSON.stringify(errors));
    } catch {
      // Ignore localStorage errors
    }
  }

  /**
   * Utility function for delays
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Configure retry behavior
   */
  configureRetry(config: Partial<RetryConfig>): void {
    this.retryConfig = { ...this.retryConfig, ...config };
  }
}

/**
 * Convenience function to get the singleton instance
 */
export const apiErrorHandler = ApiErrorHandler.getInstance();

/**
 * HOF for wrapping fetch calls with error handling
 */
export function withApiErrorHandling(
  fetcher: (url: string, options?: RequestInit) => Promise<Response>
) {
  return async (url: string, options?: RequestInit): Promise<Response> => {
    try {
      const response = await fetcher(url, options);
      return response;
    } catch (error) {
      throw apiErrorHandler['normalizeError'](error);
    }
  };
}

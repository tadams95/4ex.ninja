'use client';

import { ApiError, apiErrorHandler } from '@/utils/error-handler';
import { errorLogger } from '@/utils/error-logging';
import { useCallback, useState } from 'react';

export interface UseApiErrorHandlerReturn {
  error: ApiError | null;
  isLoading: boolean;
  isRetrying: boolean;
  retryCount: number;
  executeWithErrorHandling: <T>(
    apiCall: () => Promise<T>,
    options?: {
      retryConfig?: {
        maxRetries?: number;
        baseDelay?: number;
        maxDelay?: number;
      };
      logContext?: {
        component?: string;
        action?: string;
      };
    }
  ) => Promise<T | null>;
  retry: () => Promise<void>;
  clearError: () => void;
}

/**
 * React hook for handling API errors with automatic retry and logging
 */
export function useApiErrorHandler(): UseApiErrorHandlerReturn {
  const [error, setError] = useState<ApiError | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [lastApiCall, setLastApiCall] = useState<(() => Promise<unknown>) | null>(null);

  const executeWithErrorHandling = useCallback(
    async <T>(
      apiCall: () => Promise<T>,
      options?: {
        retryConfig?: {
          maxRetries?: number;
          baseDelay?: number;
          maxDelay?: number;
        };
        logContext?: {
          component?: string;
          action?: string;
        };
      }
    ): Promise<T | null> => {
      setIsLoading(true);
      setError(null);
      setLastApiCall(() => apiCall);

      try {
        const result = await apiErrorHandler.withRetry(apiCall, options?.retryConfig);
        setRetryCount(0);
        return result;
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError);

        // Log the error with context
        errorLogger.logApiError(
          apiError.message,
          apiError.endpoint || 'unknown',
          'unknown',
          apiError.status,
          options?.logContext
        );

        return null;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const retry = useCallback(async () => {
    if (!lastApiCall || isRetrying) return;

    setIsRetrying(true);
    setRetryCount(prev => prev + 1);

    try {
      await lastApiCall();
      setError(null);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
    } finally {
      setIsRetrying(false);
    }
  }, [lastApiCall, isRetrying]);

  const clearError = useCallback(() => {
    setError(null);
    setRetryCount(0);
  }, []);

  return {
    error,
    isLoading,
    isRetrying,
    retryCount,
    executeWithErrorHandling,
    retry,
    clearError,
  };
}

/**
 * Hook for handling fetch requests with built-in error handling
 */
export function useApiRequest() {
  const { executeWithErrorHandling, ...rest } = useApiErrorHandler();

  const get = useCallback(
    async <T>(
      url: string,
      options?: RequestInit & { logContext?: { component?: string; action?: string } }
    ): Promise<T | null> => {
      const { logContext, ...fetchOptions } = options || {};

      return executeWithErrorHandling(
        async () => {
          const response = await fetch(url, {
            method: 'GET',
            ...fetchOptions,
          });
          return apiErrorHandler.handleResponse<T>(response, url);
        },
        { logContext }
      );
    },
    [executeWithErrorHandling]
  );

  const post = useCallback(
    async <T>(
      url: string,
      data?: unknown,
      options?: RequestInit & { logContext?: { component?: string; action?: string } }
    ): Promise<T | null> => {
      const { logContext, ...fetchOptions } = options || {};

      return executeWithErrorHandling(
        async () => {
          const response = await fetch(url, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...fetchOptions.headers,
            },
            body: data ? JSON.stringify(data) : undefined,
            ...fetchOptions,
          });
          return apiErrorHandler.handleResponse<T>(response, url);
        },
        { logContext }
      );
    },
    [executeWithErrorHandling]
  );

  const put = useCallback(
    async <T>(
      url: string,
      data?: unknown,
      options?: RequestInit & { logContext?: { component?: string; action?: string } }
    ): Promise<T | null> => {
      const { logContext, ...fetchOptions } = options || {};

      return executeWithErrorHandling(
        async () => {
          const response = await fetch(url, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              ...fetchOptions.headers,
            },
            body: data ? JSON.stringify(data) : undefined,
            ...fetchOptions,
          });
          return apiErrorHandler.handleResponse<T>(response, url);
        },
        { logContext }
      );
    },
    [executeWithErrorHandling]
  );

  const del = useCallback(
    async <T>(
      url: string,
      options?: RequestInit & { logContext?: { component?: string; action?: string } }
    ): Promise<T | null> => {
      const { logContext, ...fetchOptions } = options || {};

      return executeWithErrorHandling(
        async () => {
          const response = await fetch(url, {
            method: 'DELETE',
            ...fetchOptions,
          });
          return apiErrorHandler.handleResponse<T>(response, url);
        },
        { logContext }
      );
    },
    [executeWithErrorHandling]
  );

  return {
    ...rest,
    get,
    post,
    put,
    delete: del,
  };
}

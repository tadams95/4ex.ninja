'use client';

import { useErrorNotification } from '@/components/error/ErrorNotificationSystem';
import { useErrorLogger } from '@/utils/error-logging';
import { useCallback } from 'react';

/**
 * Hook that combines error logging with user notifications
 * Provides a unified interface for handling errors across the app
 */
export function useErrorHandler() {
  const { addError, addWarning, addInfo } = useErrorNotification();
  const { logError, logWarning, logComponentError, logApiError } = useErrorLogger();

  const handleError = useCallback(
    (
      error: Error | string,
      options?: {
        title?: string;
        showNotification?: boolean;
        component?: string;
        context?: Record<string, unknown>;
        action?: {
          label: string;
          handler: () => void;
        };
      }
    ) => {
      const errorMessage = typeof error === 'string' ? error : error.message;
      const title = options?.title || 'An error occurred';

      // Log the error
      if (options?.component) {
        logComponentError(error, options.component, options?.context);
      } else {
        logError(error, undefined, options?.context);
      }

      // Show notification if requested (default: true)
      if (options?.showNotification !== false) {
        addError(title, errorMessage, options?.action);
      }
    },
    [addError, logError, logComponentError]
  );

  const handleApiError = useCallback(
    (
      error: Error | string,
      endpoint: string,
      method: string = 'GET',
      options?: {
        title?: string;
        showNotification?: boolean;
        statusCode?: number;
        requestData?: unknown;
        retryAction?: () => void;
      }
    ) => {
      const errorMessage = typeof error === 'string' ? error : error.message;
      const title = options?.title || 'Request failed';

      // Log the API error
      logApiError(error, endpoint, method, options?.statusCode, options?.requestData);

      // Show notification if requested (default: true)
      if (options?.showNotification !== false) {
        const action = options?.retryAction
          ? {
              label: 'Retry',
              handler: options.retryAction,
            }
          : undefined;

        addError(title, errorMessage, action);
      }
    },
    [addError, logApiError]
  );

  const handleWarning = useCallback(
    (
      message: string,
      options?: {
        title?: string;
        showNotification?: boolean;
        component?: string;
        context?: Record<string, unknown>;
        action?: {
          label: string;
          handler: () => void;
        };
      }
    ) => {
      const title = options?.title || 'Warning';

      // Log the warning
      logWarning(
        message,
        options?.component ? { component: options.component } : undefined,
        options?.context
      );

      // Show notification if requested (default: true)
      if (options?.showNotification !== false) {
        addWarning(title, message, options?.action);
      }
    },
    [addWarning, logWarning]
  );

  const handleInfo = useCallback(
    (
      message: string,
      options?: {
        title?: string;
        showNotification?: boolean;
        component?: string;
        context?: Record<string, unknown>;
        action?: {
          label: string;
          handler: () => void;
        };
      }
    ) => {
      const title = options?.title || 'Information';

      // Show notification if requested (default: true)
      if (options?.showNotification !== false) {
        addInfo(title, message, options?.action);
      }
    },
    [addInfo]
  );

  const handleNetworkError = useCallback(
    (
      error: Error | string,
      options?: {
        title?: string;
        showNotification?: boolean;
        retryAction?: () => void;
      }
    ) => {
      const errorMessage = typeof error === 'string' ? error : error.message;
      const title = options?.title || 'Connection problem';

      // Log the network error
      logError(error, { action: 'NETWORK_ERROR' });

      // Show notification with retry action
      if (options?.showNotification !== false) {
        const action = options?.retryAction
          ? {
              label: 'Retry',
              handler: options.retryAction,
            }
          : undefined;

        addError(title, errorMessage, action);
      }
    },
    [addError, logError]
  );

  const handleAuthError = useCallback(
    (
      error: Error | string,
      options?: {
        title?: string;
        showNotification?: boolean;
        redirectToLogin?: boolean;
      }
    ) => {
      const errorMessage = typeof error === 'string' ? error : error.message;
      const title = options?.title || 'Authentication required';

      // Log the auth error
      logError(error, { action: 'AUTH_ERROR' });

      // Show notification with login action
      if (options?.showNotification !== false) {
        const action =
          options?.redirectToLogin !== false
            ? {
                label: 'Login',
                handler: () => (window.location.href = '/login'),
              }
            : undefined;

        addError(title, errorMessage, action);
      }
    },
    [addError, logError]
  );

  return {
    handleError,
    handleApiError,
    handleWarning,
    handleInfo,
    handleNetworkError,
    handleAuthError,
  };
}

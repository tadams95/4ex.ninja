'use client';

import { createContext, ReactNode, useCallback, useContext, useState } from 'react';

export interface ErrorNotification {
  id: string;
  type: 'error' | 'warning' | 'info';
  title: string;
  message: string;
  action?: {
    label: string;
    handler: () => void;
  };
  dismissible?: boolean;
  autoHide?: boolean;
  duration?: number; // ms
  timestamp: Date;
}

interface ErrorNotificationContextType {
  notifications: ErrorNotification[];
  addNotification: (notification: Omit<ErrorNotification, 'id' | 'timestamp'>) => string;
  removeNotification: (id: string) => void;
  clearAllNotifications: () => void;
  addError: (title: string, message: string, action?: ErrorNotification['action']) => string;
  addWarning: (title: string, message: string, action?: ErrorNotification['action']) => string;
  addInfo: (title: string, message: string, action?: ErrorNotification['action']) => string;
}

const ErrorNotificationContext = createContext<ErrorNotificationContextType | null>(null);

export function useErrorNotification() {
  const context = useContext(ErrorNotificationContext);
  if (!context) {
    throw new Error('useErrorNotification must be used within ErrorNotificationProvider');
  }
  return context;
}

interface ErrorNotificationProviderProps {
  children: ReactNode;
  maxNotifications?: number;
}

export function ErrorNotificationProvider({
  children,
  maxNotifications = 5,
}: ErrorNotificationProviderProps) {
  const [notifications, setNotifications] = useState<ErrorNotification[]>([]);

  const addNotification = useCallback(
    (notification: Omit<ErrorNotification, 'id' | 'timestamp'>): string => {
      const id = `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const newNotification: ErrorNotification = {
        ...notification,
        id,
        timestamp: new Date(),
        dismissible: notification.dismissible ?? true,
        autoHide: notification.autoHide ?? true,
        duration: notification.duration ?? 5000,
      };

      setNotifications(prev => {
        const updated = [newNotification, ...prev];
        // Limit number of notifications
        return updated.slice(0, maxNotifications);
      });

      // Auto-hide if specified
      if (newNotification.autoHide) {
        setTimeout(() => {
          removeNotification(id);
        }, newNotification.duration);
      }

      return id;
    },
    [maxNotifications]
  );

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);

  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  const addError = useCallback(
    (title: string, message: string, action?: ErrorNotification['action']): string => {
      return addNotification({
        type: 'error',
        title,
        message,
        action,
        autoHide: false, // Errors should be manually dismissed
        dismissible: true,
      });
    },
    [addNotification]
  );

  const addWarning = useCallback(
    (title: string, message: string, action?: ErrorNotification['action']): string => {
      return addNotification({
        type: 'warning',
        title,
        message,
        action,
        autoHide: true,
        duration: 7000, // Warnings stay longer
      });
    },
    [addNotification]
  );

  const addInfo = useCallback(
    (title: string, message: string, action?: ErrorNotification['action']): string => {
      return addNotification({
        type: 'info',
        title,
        message,
        action,
        autoHide: true,
        duration: 4000,
      });
    },
    [addNotification]
  );

  const contextValue: ErrorNotificationContextType = {
    notifications,
    addNotification,
    removeNotification,
    clearAllNotifications,
    addError,
    addWarning,
    addInfo,
  };

  return (
    <ErrorNotificationContext.Provider value={contextValue}>
      {children}
      <ErrorNotificationDisplay />
    </ErrorNotificationContext.Provider>
  );
}

function ErrorNotificationDisplay() {
  const { notifications, removeNotification } = useErrorNotification();

  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm w-full">
      {notifications.map(notification => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          onDismiss={() => removeNotification(notification.id)}
        />
      ))}
    </div>
  );
}

interface NotificationItemProps {
  notification: ErrorNotification;
  onDismiss: () => void;
}

function NotificationItem({ notification, onDismiss }: NotificationItemProps) {
  const { type, title, message, action, dismissible } = notification;

  const getTypeStyles = () => {
    switch (type) {
      case 'error':
        return {
          container: 'bg-red-50 border-red-200',
          icon: 'text-red-400',
          title: 'text-red-800',
          message: 'text-red-700',
          button: 'text-red-800 hover:bg-red-100 focus:ring-red-500',
        };
      case 'warning':
        return {
          container: 'bg-yellow-50 border-yellow-200',
          icon: 'text-yellow-400',
          title: 'text-yellow-800',
          message: 'text-yellow-700',
          button: 'text-yellow-800 hover:bg-yellow-100 focus:ring-yellow-500',
        };
      case 'info':
        return {
          container: 'bg-blue-50 border-blue-200',
          icon: 'text-blue-400',
          title: 'text-blue-800',
          message: 'text-blue-700',
          button: 'text-blue-800 hover:bg-blue-100 focus:ring-blue-500',
        };
    }
  };

  const styles = getTypeStyles();

  const getIcon = () => {
    switch (type) {
      case 'error':
        return (
          <svg className={`h-5 w-5 ${styles.icon}`} viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'warning':
        return (
          <svg className={`h-5 w-5 ${styles.icon}`} viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'info':
        return (
          <svg className={`h-5 w-5 ${styles.icon}`} viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
        );
    }
  };

  return (
    <div className={`rounded-lg border p-4 shadow-lg ${styles.container}`}>
      <div className="flex">
        <div className="flex-shrink-0">{getIcon()}</div>
        <div className="ml-3 flex-1">
          <h4 className={`text-sm font-medium ${styles.title}`}>{title}</h4>
          <div className={`mt-1 text-sm ${styles.message}`}>
            <p>{message}</p>
          </div>
          {action && (
            <div className="mt-3">
              <button
                type="button"
                onClick={action.handler}
                className={`rounded-md px-3 py-1 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 ${styles.button}`}
              >
                {action.label}
              </button>
            </div>
          )}
        </div>
        {dismissible && (
          <div className="ml-4 flex-shrink-0">
            <button
              type="button"
              onClick={onDismiss}
              className={`rounded-md inline-flex p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2 ${styles.button}`}
            >
              <span className="sr-only">Dismiss</span>
              <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

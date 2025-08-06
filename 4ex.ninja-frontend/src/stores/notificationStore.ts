'use client';

import { NotificationSettings } from '@/types';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

interface ToastNotification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number; // in milliseconds, 0 for persistent
  action?: {
    label: string;
    onClick: () => void;
  };
  createdAt: Date;
}

interface NotificationState {
  // Toast notification queue
  toasts: ToastNotification[];
  maxToasts: number;

  // User notification preferences
  settings: NotificationSettings;
  settingsLoading: boolean;
  settingsError: string | null;

  // Error notifications from API calls
  apiErrors: Record<string, string>; // key: endpoint/action, value: error message

  // Browser notification permission
  browserPermission: NotificationPermission | null;

  // Actions for toast management
  addToast: (toast: Omit<ToastNotification, 'id' | 'createdAt'>) => void;
  removeToast: (id: string) => void;
  clearAllToasts: () => void;

  // Actions for notification settings
  updateSettings: (settings: Partial<NotificationSettings>) => void;
  setSettingsLoading: (loading: boolean) => void;
  setSettingsError: (error: string | null) => void;
  resetSettings: () => void;

  // Actions for API error tracking
  setApiError: (key: string, error: string) => void;
  clearApiError: (key: string) => void;
  clearAllApiErrors: () => void;

  // Browser notification actions
  requestBrowserPermission: () => Promise<NotificationPermission>;
  setBrowserPermission: (permission: NotificationPermission) => void;

  // Utility actions
  showSuccessToast: (title: string, message?: string) => void;
  showErrorToast: (title: string, message?: string) => void;
  showWarningToast: (title: string, message?: string) => void;
  showInfoToast: (title: string, message?: string) => void;

  reset: () => void;
}

const defaultSettings: NotificationSettings = {
  emailNotifications: true,
  pushNotifications: false,
  smsNotifications: false,
  emailFrequency: 'immediate',
  notificationTypes: {
    crossoverAlerts: true,
    marketUpdates: true,
    accountUpdates: true,
    promotional: false,
  },
  preferredPairs: [],
  minimumSignalStrength: 1,
};

const initialState = {
  toasts: [],
  maxToasts: 5,
  settings: defaultSettings,
  settingsLoading: false,
  settingsError: null,
  apiErrors: {},
  browserPermission: null,
};

let toastCounter = 0;

export const useNotificationStore = create<NotificationState>()(
  devtools(
    persist(
      immer((set, get) => ({
        ...initialState,

        addToast: (toast: Omit<ToastNotification, 'id' | 'createdAt'>) =>
          set(state => {
            const newToast: ToastNotification = {
              ...toast,
              id: `toast-${++toastCounter}`,
              createdAt: new Date(),
              duration: toast.duration ?? 5000, // Default 5 seconds
            };

            state.toasts.push(newToast);

            // Remove oldest toasts if we exceed maxToasts
            if (state.toasts.length > state.maxToasts) {
              state.toasts = state.toasts.slice(-state.maxToasts);
            }

            // Auto-remove toast after duration if not persistent
            if (newToast.duration && newToast.duration > 0) {
              setTimeout(() => {
                get().removeToast(newToast.id);
              }, newToast.duration);
            }
          }),

        removeToast: (id: string) =>
          set(state => {
            state.toasts = state.toasts.filter(toast => toast.id !== id);
          }),

        clearAllToasts: () =>
          set(state => {
            state.toasts = [];
          }),

        updateSettings: (settings: Partial<NotificationSettings>) =>
          set(state => {
            state.settings = { ...state.settings, ...settings };
            state.settingsError = null;
          }),

        setSettingsLoading: (loading: boolean) =>
          set(state => {
            state.settingsLoading = loading;
          }),

        setSettingsError: (error: string | null) =>
          set(state => {
            state.settingsError = error;
          }),

        resetSettings: () =>
          set(state => {
            state.settings = defaultSettings;
            state.settingsError = null;
          }),

        setApiError: (key: string, error: string) =>
          set(state => {
            state.apiErrors[key] = error;
          }),

        clearApiError: (key: string) =>
          set(state => {
            delete state.apiErrors[key];
          }),

        clearAllApiErrors: () =>
          set(state => {
            state.apiErrors = {};
          }),

        requestBrowserPermission: async () => {
          if (!('Notification' in window)) {
            set(state => {
              state.browserPermission = 'denied';
            });
            return 'denied';
          }

          const permission = await Notification.requestPermission();
          set(state => {
            state.browserPermission = permission;
          });
          return permission;
        },

        setBrowserPermission: (permission: NotificationPermission) =>
          set(state => {
            state.browserPermission = permission;
          }),

        showSuccessToast: (title: string, message?: string) =>
          get().addToast({
            type: 'success',
            title,
            message,
          }),

        showErrorToast: (title: string, message?: string) =>
          get().addToast({
            type: 'error',
            title,
            message,
            duration: 8000, // Longer duration for errors
          }),

        showWarningToast: (title: string, message?: string) =>
          get().addToast({
            type: 'warning',
            title,
            message,
            duration: 6000,
          }),

        showInfoToast: (title: string, message?: string) =>
          get().addToast({
            type: 'info',
            title,
            message,
          }),

        reset: () =>
          set(state => {
            Object.assign(state, initialState);
          }),
      })),
      {
        name: 'notification-store',
        // Persist user preferences and browser permission, but not toasts or errors
        partialize: state => ({
          settings: state.settings,
          browserPermission: state.browserPermission,
          maxToasts: state.maxToasts,
        }),
      }
    ),
    {
      name: 'notification-store',
    }
  )
);

// Selectors for common use cases
export const useToasts = () => useNotificationStore(state => state.toasts);
export const useNotificationSettings = () => useNotificationStore(state => state.settings);
export const useNotificationSettingsState = () =>
  useNotificationStore(state => ({
    settings: state.settings,
    loading: state.settingsLoading,
    error: state.settingsError,
  }));
export const useApiErrors = () => useNotificationStore(state => state.apiErrors);
export const useBrowserPermission = () => useNotificationStore(state => state.browserPermission);

// Toast action selectors
export const useToastActions = () =>
  useNotificationStore(state => ({
    showSuccess: state.showSuccessToast,
    showError: state.showErrorToast,
    showWarning: state.showWarningToast,
    showInfo: state.showInfoToast,
    remove: state.removeToast,
    clearAll: state.clearAllToasts,
  }));

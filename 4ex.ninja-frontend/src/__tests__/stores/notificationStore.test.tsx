import { act, renderHook } from '@testing-library/react';
import { useNotificationStore } from '../../stores/notificationStore';

// Mock notification data matching actual interfaces
const mockToast = {
  type: 'success' as const,
  title: 'Success',
  message: 'Operation completed successfully',
  duration: 5000,
};

describe('notificationStore - Core Functionality', () => {
  beforeEach(() => {
    // Reset store before each test
    useNotificationStore.getState().reset();
  });

  describe('Toast notifications', () => {
    it('should initialize with default state', () => {
      const { result } = renderHook(() => useNotificationStore());

      expect(result.current.toasts).toEqual([]);
      expect(result.current.maxToasts).toBe(5);
    });

    it('should add toast notification', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.addToast(mockToast);
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].title).toBe('Success');
      expect(result.current.toasts[0].type).toBe('success');
    });

    it('should remove toast notification', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.addToast(mockToast);
      });

      const toastId = result.current.toasts[0].id;

      act(() => {
        result.current.removeToast(toastId);
      });

      expect(result.current.toasts).toHaveLength(0);
    });

    it('should clear all toasts', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.addToast(mockToast);
        result.current.addToast({ ...mockToast, title: 'Another Toast' });
      });

      expect(result.current.toasts).toHaveLength(2);

      act(() => {
        result.current.clearAllToasts();
      });

      expect(result.current.toasts).toHaveLength(0);
    });

    it('should show success toast', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.showSuccessToast('Success Title', 'Success message');
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].type).toBe('success');
      expect(result.current.toasts[0].title).toBe('Success Title');
    });

    it('should show error toast', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.showErrorToast('Error Title', 'Error message');
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].type).toBe('error');
      expect(result.current.toasts[0].title).toBe('Error Title');
    });
  });

  describe('Notification settings', () => {
    it('should initialize with default settings', () => {
      const { result } = renderHook(() => useNotificationStore());

      expect(result.current.settings.emailNotifications).toBe(true);
      expect(result.current.settings.pushNotifications).toBe(false);
      expect(result.current.settings.emailFrequency).toBe('immediate');
    });

    it('should update notification settings', () => {
      const { result } = renderHook(() => useNotificationStore());

      const newSettings = {
        emailNotifications: false,
        pushNotifications: true,
        emailFrequency: 'daily' as const,
      };

      act(() => {
        result.current.updateSettings(newSettings);
      });

      expect(result.current.settings.emailNotifications).toBe(false);
      expect(result.current.settings.pushNotifications).toBe(true);
      expect(result.current.settings.emailFrequency).toBe('daily');
    });

    it('should handle settings loading state', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.setSettingsLoading(true);
      });

      expect(result.current.settingsLoading).toBe(true);
    });

    it('should handle settings error state', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.setSettingsError('Failed to save settings');
      });

      expect(result.current.settingsError).toBe('Failed to save settings');
    });

    it('should reset settings', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.updateSettings({ emailNotifications: false });
        result.current.setSettingsError('Some error');
      });

      act(() => {
        result.current.resetSettings();
      });

      expect(result.current.settings.emailNotifications).toBe(true);
      expect(result.current.settingsError).toBeNull();
    });
  });

  describe('API error tracking', () => {
    it('should set API error', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.setApiError('crossovers', 'Failed to load crossovers');
      });

      expect(result.current.apiErrors['crossovers']).toBe('Failed to load crossovers');
    });

    it('should clear specific API error', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.setApiError('crossovers', 'Failed to load crossovers');
      });

      act(() => {
        result.current.clearApiError('crossovers');
      });

      expect(result.current.apiErrors['crossovers']).toBeUndefined();
    });

    it('should clear all API errors', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.setApiError('crossovers', 'Error 1');
        result.current.setApiError('user', 'Error 2');
      });

      act(() => {
        result.current.clearAllApiErrors();
      });

      expect(Object.keys(result.current.apiErrors)).toHaveLength(0);
    });
  });

  describe('Browser permission management', () => {
    it('should update browser permission status', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.setBrowserPermission('granted');
      });

      expect(result.current.browserPermission).toBe('granted');
    });
  });

  describe('Store utilities', () => {
    it('should reset to initial state', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.addToast(mockToast);
        result.current.setApiError('test', 'Test error');
        result.current.updateSettings({ emailNotifications: false });
        result.current.setBrowserPermission('granted');
      });

      act(() => {
        result.current.reset();
      });

      expect(result.current.toasts).toEqual([]);
      expect(Object.keys(result.current.apiErrors)).toHaveLength(0);
      expect(result.current.settings.emailNotifications).toBe(true);
      expect(result.current.browserPermission).toBeNull();
    });
  });
});

describe('notificationStore - Selectors', () => {
  beforeEach(() => {
    useNotificationStore.getState().reset();
  });

  it('should provide toasts selector', () => {
    const { result } = renderHook(() => useNotificationStore(state => state.toasts));

    expect(result.current).toEqual([]);

    act(() => {
      useNotificationStore.getState().addToast(mockToast);
    });

    expect(result.current).toHaveLength(1);
    expect(result.current[0].title).toBe('Success');
  });

  it('should provide settings selector', () => {
    const { result } = renderHook(() =>
      useNotificationStore(state => state.settings.emailNotifications)
    );

    expect(result.current).toBe(true);

    act(() => {
      useNotificationStore.getState().updateSettings({
        emailNotifications: false,
      });
    });

    expect(result.current).toBe(false);
  });

  it('should provide API errors selector', () => {
    const { result } = renderHook(() => useNotificationStore(state => state.apiErrors));

    expect(Object.keys(result.current)).toHaveLength(0);

    act(() => {
      useNotificationStore.getState().setApiError('test', 'Test error');
    });

    expect(result.current['test']).toBe('Test error');
  });

  it('should provide browser permission selector', () => {
    const { result } = renderHook(() => useNotificationStore(state => state.browserPermission));

    expect(result.current).toBeNull();

    act(() => {
      useNotificationStore.getState().setBrowserPermission('granted');
    });

    expect(result.current).toBe('granted');
  });
});

import { act, renderHook } from '@testing-library/react';
import { useUserStore } from '../../stores/userStore';

// Mock user data
const mockUser = {
  id: 'user123',
  name: 'John Doe',
  email: 'john@example.com',
  isSubscribed: true,
  subscriptionEnds: new Date('2024-12-31'),
};

describe('userStore - Core Functionality', () => {
  beforeEach(() => {
    // Reset store before each test
    useUserStore.getState().reset();
  });

  describe('User authentication state', () => {
    it('should initialize with default state', () => {
      const { result } = renderHook(() => useUserStore());

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.authLoading).toBe(true);
    });

    it('should set user and authentication state', () => {
      const { result } = renderHook(() => useUserStore());

      act(() => {
        result.current.setUser(mockUser);
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
    });

    it('should clear user state', () => {
      const { result } = renderHook(() => useUserStore());

      act(() => {
        result.current.setUser(mockUser);
      });

      act(() => {
        result.current.clearUser();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.isSubscribed).toBe(false);
    });
  });

  describe('Subscription management', () => {
    it('should update subscription status', () => {
      const { result } = renderHook(() => useUserStore());

      act(() => {
        result.current.setSubscriptionStatus(true, '2024-12-31');
      });

      expect(result.current.isSubscribed).toBe(true);
      expect(result.current.subscriptionEnds).toEqual(new Date('2024-12-31'));
    });

    it('should handle subscription loading state', () => {
      const { result } = renderHook(() => useUserStore());

      act(() => {
        result.current.setSubscriptionLoading(true);
      });

      expect(result.current.subscriptionLoading).toBe(true);
    });
  });

  describe('Profile management', () => {
    it('should update user profile', () => {
      const { result } = renderHook(() => useUserStore());

      act(() => {
        result.current.setUser(mockUser);
      });

      act(() => {
        result.current.updateProfile({ name: 'Jane Doe' });
      });

      expect(result.current.user?.name).toBe('Jane Doe');
      expect(result.current.user?.email).toBe('john@example.com'); // Other fields preserved
    });

    it('should handle profile loading and error states', () => {
      const { result } = renderHook(() => useUserStore());

      act(() => {
        result.current.setProfileLoading(true);
      });

      expect(result.current.profileLoading).toBe(true);

      act(() => {
        result.current.setProfileError('Update failed');
      });

      expect(result.current.profileError).toBe('Update failed');
    });
  });

  describe('Store utilities', () => {
    it('should reset to initial state', () => {
      const { result } = renderHook(() => useUserStore());

      act(() => {
        result.current.setUser(mockUser);
        result.current.setProfileError('Some error');
      });

      act(() => {
        result.current.reset();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.profileError).toBeNull();
    });
  });
});

describe('userStore - Selectors', () => {
  beforeEach(() => {
    useUserStore.getState().reset();
  });

  it('should provide user selector', () => {
    const { result } = renderHook(() => useUserStore(state => state.user));

    expect(result.current).toBeNull();

    act(() => {
      useUserStore.getState().setUser(mockUser);
    });

    expect(result.current).toEqual(mockUser);
  });

  it('should provide authentication status selector', () => {
    const { result } = renderHook(() => useUserStore(state => state.isAuthenticated));

    expect(result.current).toBe(false);

    act(() => {
      useUserStore.getState().setUser(mockUser);
    });

    expect(result.current).toBe(true);
  });

  it('should provide subscription status selector', () => {
    const { result } = renderHook(() => useUserStore(state => state.isSubscribed));

    expect(result.current).toBe(false);

    act(() => {
      useUserStore.getState().setSubscriptionStatus(true, '2024-12-31');
    });

    expect(result.current).toBe(true);
  });
});

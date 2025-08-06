import '@testing-library/jest-dom';

// Polyfills for Node.js environment
const { TextEncoder, TextDecoder } = require('util');
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

// MSW Server setup - temporarily disabled until polyfill issues are resolved
// TODO: Re-enable MSW in next iteration
// import 'whatwg-fetch'
// import { server } from './src/mocks/server'

// Establish API mocking before all tests.
// beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))

// Reset any request handlers that we may add during the tests,
// so they don't affect other tests.
// afterEach(() => server.resetHandlers())

// Clean up after the tests are finished.
// afterAll(() => server.close())

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/',
      pathname: '/',
      query: {},
      asPath: '/',
      push: jest.fn(),
      pop: jest.fn(),
      reload: jest.fn(),
      back: jest.fn(),
      prefetch: jest.fn(),
      beforePopState: jest.fn(),
      events: {
        on: jest.fn(),
        off: jest.fn(),
        emit: jest.fn(),
      },
    };
  },
}));

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
    };
  },
  useSearchParams() {
    return new URLSearchParams();
  },
  usePathname() {
    return '/';
  },
}));

// Mock NextAuth
jest.mock('next-auth/react', () => ({
  useSession() {
    return {
      data: null,
      status: 'unauthenticated',
      update: jest.fn(),
    };
  },
  signIn: jest.fn(),
  signOut: jest.fn(),
  getSession: jest.fn(),
  SessionProvider: ({ children }) => children,
}));

// Mock Zustand stores (will be uncommented when stores are created)
// jest.mock('@/stores/userStore', () => ({
//   useUserStore: jest.fn(() => ({
//     user: null,
//     isAuthenticated: false,
//     isSubscribed: false,
//     setUser: jest.fn(),
//     setSubscriptionStatus: jest.fn(),
//     clearUser: jest.fn(),
//   })),
// }))

// jest.mock('@/stores/crossoverStore', () => ({
//   useCrossoverStore: jest.fn(() => ({
//     crossovers: [],
//     loading: false,
//     error: null,
//     setCrossovers: jest.fn(),
//     setLoading: jest.fn(),
//     setError: jest.fn(),
//   })),
// }))

// jest.mock('@/stores/notificationStore', () => ({
//   useNotificationStore: jest.fn(() => ({
//     notifications: [],
//     addNotification: jest.fn(),
//     removeNotification: jest.fn(),
//     clearNotifications: jest.fn(),
//   })),
// }))

// Global test utilities
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

/**
 * Service Worker registration and management for asset optimization
 */

let serviceWorkerRegistration: ServiceWorkerRegistration | null = null;

/**
 * Register the service worker for asset optimization
 */
export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    console.log('Service Worker not supported');
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/',
    });

    serviceWorkerRegistration = registration;

    // Handle service worker updates
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      if (newWorker) {
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            // New service worker is available
            console.log('New service worker available');

            // Optionally notify user about update
            if (typeof window !== 'undefined' && 'dispatchEvent' in window) {
              window.dispatchEvent(new CustomEvent('sw-update-available'));
            }
          }
        });
      }
    });

    console.log('Service Worker registered successfully');
    return registration;
  } catch (error) {
    console.error('Service Worker registration failed:', error);
    return null;
  }
}

/**
 * Unregister the service worker
 */
export async function unregisterServiceWorker(): Promise<boolean> {
  if (!serviceWorkerRegistration) {
    return false;
  }

  try {
    const success = await serviceWorkerRegistration.unregister();
    serviceWorkerRegistration = null;
    console.log('Service Worker unregistered successfully');
    return success;
  } catch (error) {
    console.error('Service Worker unregistration failed:', error);
    return false;
  }
}

/**
 * Check if service worker is active
 */
export function isServiceWorkerActive(): boolean {
  return !!(serviceWorkerRegistration && navigator.serviceWorker.controller);
}

/**
 * Send message to service worker
 */
export function sendMessageToServiceWorker(message: { type: string; payload?: any }): Promise<any> {
  return new Promise((resolve, reject) => {
    if (!navigator.serviceWorker.controller) {
      reject(new Error('No active service worker'));
      return;
    }

    const messageChannel = new MessageChannel();
    messageChannel.port1.onmessage = event => {
      resolve(event.data);
    };

    navigator.serviceWorker.controller.postMessage(message, [messageChannel.port2]);
  });
}

/**
 * Preload images through service worker
 */
export async function preloadImages(imageUrls: string[]): Promise<void> {
  if (!isServiceWorkerActive()) {
    console.warn('Service Worker not active, cannot preload images');
    return;
  }

  try {
    await sendMessageToServiceWorker({
      type: 'PRELOAD_IMAGES',
      payload: imageUrls,
    });
    console.log('Images preloaded successfully');
  } catch (error) {
    console.error('Failed to preload images:', error);
  }
}

/**
 * Clear service worker cache
 */
export async function clearServiceWorkerCache(cacheType?: string): Promise<void> {
  if (!isServiceWorkerActive()) {
    console.warn('Service Worker not active, cannot clear cache');
    return;
  }

  try {
    await sendMessageToServiceWorker({
      type: 'CLEAR_CACHE',
      payload: cacheType,
    });
    console.log('Cache cleared successfully');
  } catch (error) {
    console.error('Failed to clear cache:', error);
  }
}

/**
 * Get cache status from service worker
 */
export async function getCacheStatus(): Promise<any> {
  if (!isServiceWorkerActive()) {
    return { error: 'Service Worker not active' };
  }

  try {
    const status = await sendMessageToServiceWorker({
      type: 'GET_CACHE_STATUS',
    });
    return status;
  } catch (error) {
    console.error('Failed to get cache status:', error);
    return { error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

/**
 * Setup service worker event listeners
 */
export function setupServiceWorkerListeners(): void {
  if (typeof window === 'undefined') return;

  // Listen for service worker updates
  window.addEventListener('sw-update-available', () => {
    console.log('Service Worker update available');

    // You can implement update notification UI here
    // For example, show a banner asking user to refresh
  });

  // Handle service worker errors
  navigator.serviceWorker?.addEventListener('error', error => {
    console.error('Service Worker error:', error);
  });

  // Handle service worker messages
  navigator.serviceWorker?.addEventListener('message', event => {
    const { type, data } = event.data;

    switch (type) {
      case 'CACHE_UPDATED':
        console.log('Cache updated:', data);
        break;
      case 'OFFLINE_READY':
        console.log('App is ready for offline use');
        break;
      default:
        console.log('Service Worker message:', event.data);
    }
  });
}

/**
 * Initialize service worker with default settings
 */
export async function initializeServiceWorker(): Promise<void> {
  if (typeof window === 'undefined') return;

  // Setup event listeners first
  setupServiceWorkerListeners();

  // Register service worker
  const registration = await registerServiceWorker();

  if (registration) {
    // Preload critical images
    const criticalImages = ['/next.svg', '/vercel.svg', '/file.svg', '/globe.svg', '/window.svg'];

    // Wait for service worker to be ready
    await navigator.serviceWorker.ready;

    // Preload critical images
    await preloadImages(criticalImages);
  }
}

/**
 * Hook for React components to use service worker
 */
export function useServiceWorker() {
  const [isActive, setIsActive] = useState(false);
  const [cacheStatus, setCacheStatus] = useState<any>(null);

  useEffect(() => {
    setIsActive(isServiceWorkerActive());

    const checkStatus = async () => {
      const status = await getCacheStatus();
      setCacheStatus(status);
    };

    if (isServiceWorkerActive()) {
      checkStatus();
    }
  }, []);

  return {
    isActive,
    cacheStatus,
    preloadImages,
    clearCache: clearServiceWorkerCache,
    getCacheStatus,
  };
}

// React hook imports (if needed)
import { useEffect, useState } from 'react';

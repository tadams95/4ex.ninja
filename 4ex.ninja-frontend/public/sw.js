/**
 * Service Worker for 4ex.ninja - Asset Optimization and Caching
 * Handles image optimization, WebP/AVIF support, and asset caching strategies
 */

const CACHE_VERSION = 'v2'; // Updated to force refresh and apply external domain fix
const STATIC_CACHE = `static-assets-${CACHE_VERSION}`;
const IMAGE_CACHE = `images-${CACHE_VERSION}`;
const API_CACHE = `api-${CACHE_VERSION}`;

// Assets to precache
const PRECACHE_ASSETS = [
  '/',
  '/manifest.json',
  '/favicon.ico',
  '/next.svg',
  '/vercel.svg',
  '/file.svg',
  '/globe.svg',
  '/window.svg',
];

// Image file extensions
const IMAGE_EXTENSIONS = /\.(jpg|jpeg|png|gif|webp|avif|svg|ico)$/i;

// Install event - precache static assets
self.addEventListener('install', event => {
  console.log('[SW] Installing service worker...');

  event.waitUntil(
    caches
      .open(STATIC_CACHE)
      .then(cache => {
        console.log('[SW] Precaching static assets');
        return cache.addAll(PRECACHE_ASSETS);
      })
      .then(() => {
        console.log('[SW] Static assets precached');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('[SW] Precaching failed:', error);
      })
  );
});

// Activate event - cleanup old caches
self.addEventListener('activate', event => {
  console.log('[SW] Activating service worker...');

  event.waitUntil(
    caches
      .keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (!cacheName.includes(CACHE_VERSION)) {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[SW] Cache cleanup complete');
        return self.clients.claim();
      })
  );
});

// Fetch event - handle requests with different strategies
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip external domains - only handle same-origin requests
  if (url.origin !== self.location.origin) {
    console.log('[SW] Skipping external request:', url.href);
    return;
  }

  console.log('[SW] Handling same-origin request:', url.pathname);

  // Handle different types of requests
  if (IMAGE_EXTENSIONS.test(url.pathname)) {
    // Image requests - cache first with WebP/AVIF optimization
    event.respondWith(handleImageRequest(request));
  } else if (url.pathname.startsWith('/api/')) {
    // API requests - network first with short-term cache
    event.respondWith(handleApiRequest(request));
  } else if (isStaticAsset(url.pathname)) {
    // Static assets - cache first
    event.respondWith(handleStaticAsset(request));
  } else {
    // Navigation requests - network first with cache fallback
    event.respondWith(handleNavigationRequest(request));
  }
});

/**
 * Handle image requests with format optimization
 */
async function handleImageRequest(request) {
  const cache = await caches.open(IMAGE_CACHE);
  const url = new URL(request.url);

  try {
    // Check cache first
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // Try to get optimized format
    const optimizedRequest = await getOptimizedImageRequest(request);
    const networkResponse = await fetch(optimizedRequest || request);

    if (networkResponse.ok) {
      // Cache the response
      await cache.put(request, networkResponse.clone());
      return networkResponse;
    }

    throw new Error(`HTTP ${networkResponse.status}`);
  } catch (error) {
    console.error('[SW] Image request failed:', error);

    // Try to return a cached version or placeholder
    const fallback =
      (await cache.match('/placeholder.svg')) ||
      new Response('Image not available', {
        status: 404,
        headers: { 'Content-Type': 'text/plain' },
      });
    return fallback;
  }
}

/**
 * Get optimized image request based on browser support
 */
async function getOptimizedImageRequest(request) {
  const url = new URL(request.url);
  const acceptHeader = request.headers.get('Accept') || '';

  // Check if browser supports modern formats
  if (acceptHeader.includes('image/avif')) {
    return getImageWithFormat(url, 'avif');
  } else if (acceptHeader.includes('image/webp')) {
    return getImageWithFormat(url, 'webp');
  }

  return null; // Use original format
}

/**
 * Generate request for image with specific format
 */
function getImageWithFormat(url, format) {
  const originalExt = url.pathname.match(/\.[^.]+$/)?.[0] || '';
  const basePath = url.pathname.replace(originalExt, '');

  // Create new URL with optimized format
  const optimizedUrl = new URL(url);
  optimizedUrl.pathname = `${basePath}.${format}`;

  return new Request(optimizedUrl.toString(), {
    headers: {
      Accept: `image/${format},image/*,*/*;q=0.8`,
    },
  });
}

/**
 * Handle API requests with network-first strategy
 */
async function handleApiRequest(request) {
  const cache = await caches.open(API_CACHE);

  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      // Cache successful responses for 5 minutes
      const responseClone = networkResponse.clone();
      const cacheResponse = new Response(responseClone.body, {
        status: responseClone.status,
        statusText: responseClone.statusText,
        headers: {
          ...Object.fromEntries(responseClone.headers.entries()),
          'sw-cached': new Date().toISOString(),
          'Cache-Control': 'max-age=300', // 5 minutes
        },
      });

      await cache.put(request, cacheResponse);
    }

    return networkResponse;
  } catch (error) {
    console.error('[SW] API request failed:', error);

    // Try to return cached response
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      // Add header to indicate stale response
      const headers = new Headers(cachedResponse.headers);
      headers.set('sw-stale', 'true');

      return new Response(cachedResponse.body, {
        status: cachedResponse.status,
        statusText: cachedResponse.statusText,
        headers,
      });
    }

    // Return meaningful offline responses for specific endpoints
    const url = new URL(request.url);
    if (url.pathname.includes('/api/crossovers')) {
      return new Response(
        JSON.stringify({
          error: 'Offline',
          message:
            'Unable to fetch latest signals while offline. Please check your internet connection.',
          crossovers: [],
          isEmpty: true,
          offline: true,
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    if (url.pathname.includes('/api/subscription-status')) {
      return new Response(
        JSON.stringify({
          error: 'Offline',
          message: 'Cannot check subscription status while offline',
          offline: true,
        }),
        {
          status: 503,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    return new Response('API not available', {
      status: 503,
      headers: { 'Content-Type': 'text/plain' },
    });
  }
}

/**
 * Handle static assets with cache-first strategy
 */
async function handleStaticAsset(request) {
  const cache = await caches.open(STATIC_CACHE);

  try {
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      await cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.error('[SW] Static asset request failed:', error);
    return new Response('Asset not available', { status: 404 });
  }
}

/**
 * Handle navigation requests with network-first strategy
 */
async function handleNavigationRequest(request) {
  try {
    const networkResponse = await fetch(request);
    return networkResponse;
  } catch (error) {
    console.error('[SW] Navigation request failed:', error);

    // Return offline page or cached version
    const cache = await caches.open(STATIC_CACHE);
    const cachedResponse =
      (await cache.match('/')) ||
      new Response('Application offline', {
        status: 503,
        headers: { 'Content-Type': 'text/plain' },
      });
    return cachedResponse;
  }
}

/**
 * Check if path is a static asset
 */
function isStaticAsset(pathname) {
  return (
    PRECACHE_ASSETS.some(asset => pathname.endsWith(asset)) ||
    pathname.startsWith('/_next/static/') ||
    pathname.startsWith('/static/') ||
    (pathname.includes('.') && !pathname.startsWith('/api/'))
  );
}

// Message handling for cache management
self.addEventListener('message', event => {
  const { type, payload } = event.data;

  switch (type) {
    case 'PRELOAD_IMAGES':
      handlePreloadImages(payload);
      break;
    case 'CLEAR_CACHE':
      handleClearCache(payload);
      break;
    case 'GET_CACHE_STATUS':
      handleGetCacheStatus(event);
      break;
    default:
      console.log('[SW] Unknown message type:', type);
  }
});

/**
 * Preload images for better performance
 */
async function handlePreloadImages(imageUrls) {
  if (!Array.isArray(imageUrls)) return;

  const cache = await caches.open(IMAGE_CACHE);

  const preloadPromises = imageUrls.map(async url => {
    try {
      const response = await fetch(url);
      if (response.ok) {
        await cache.put(url, response);
        console.log('[SW] Preloaded image:', url);
      }
    } catch (error) {
      console.error('[SW] Failed to preload image:', url, error);
    }
  });

  await Promise.allSettled(preloadPromises);
}

/**
 * Clear specific cache or all caches
 */
async function handleClearCache(cacheType) {
  try {
    if (cacheType) {
      const cacheName = `${cacheType}-${CACHE_VERSION}`;
      await caches.delete(cacheName);
      console.log('[SW] Cleared cache:', cacheName);
    } else {
      const cacheNames = await caches.keys();
      await Promise.all(cacheNames.map(name => caches.delete(name)));
      console.log('[SW] Cleared all caches');
    }
  } catch (error) {
    console.error('[SW] Failed to clear cache:', error);
  }
}

/**
 * Get cache status information
 */
async function handleGetCacheStatus(event) {
  try {
    const cacheNames = await caches.keys();
    const status = {
      caches: cacheNames,
      version: CACHE_VERSION,
      timestamp: new Date().toISOString(),
    };

    event.ports[0]?.postMessage(status);
  } catch (error) {
    console.error('[SW] Failed to get cache status:', error);
    event.ports[0]?.postMessage({ error: error.message });
  }
}

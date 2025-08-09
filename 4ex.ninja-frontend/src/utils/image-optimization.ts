/**
 * Asset optimization utilities for WebP/AVIF support and progressive loading
 */

/**
 * Check if the browser supports WebP format
 */
export function supportsWebP(): Promise<boolean> {
  return new Promise(resolve => {
    if (typeof window === 'undefined') {
      resolve(false);
      return;
    }

    const webP = new Image();
    webP.onload = webP.onerror = () => {
      resolve(webP.height === 2);
    };
    webP.src =
      'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
  });
}

/**
 * Check if the browser supports AVIF format
 */
export function supportsAVIF(): Promise<boolean> {
  return new Promise(resolve => {
    if (typeof window === 'undefined') {
      resolve(false);
      return;
    }

    const avif = new Image();
    avif.onload = avif.onerror = () => {
      resolve(avif.height === 2);
    };
    avif.src =
      'data:image/avif;base64,AAAAIGZ0eXBhdmlmAAAAAGF2aWZtaWYxbWlhZk1BMUIAAADybWV0YQAAAAAAAAAoaGRscgAAAAAAAAAAcGljdAAAAAAAAAAAAAAAAGxpYmF2aWYAAAAADnBpdG0AAAAAAAEAAAAeaWxvYwAAAABEAAABAAEAAAABAAABGgAAABcAAAAoaWluZgAAAAAAAQAAABppbmZlAgAAAAABAABhdjAxQ29sb3IAAAAAamlwcnAAAABLaXBjbwAAABRpc3BlAAAAAAAAAAEAAAABAAAAEHBpeGkAAAAAAwgICAAAAAxhdjFDgQAMAAAAABNjb2xybmNseAACAAIABoAAAAAXaXBtYQAAAAAAAAABAAEEAQKDBAAAAB9tZGF0EgAKCBgABogQEDQgMgkQAAAAB8dSLfI=';
  });
}

/**
 * Get the optimal image format based on browser support
 */
export async function getOptimalImageFormat(): Promise<'avif' | 'webp' | 'jpg'> {
  if (await supportsAVIF()) {
    return 'avif';
  }
  if (await supportsWebP()) {
    return 'webp';
  }
  return 'jpg';
}

/**
 * Generate srcSet for responsive images with modern formats
 */
export function generateSrcSet(
  src: string,
  sizes: number[] = [640, 750, 828, 1080, 1200, 1920],
  format?: 'avif' | 'webp' | 'jpg'
): string {
  if (!format) {
    // Fallback to original image
    return sizes.map(size => `${src}?w=${size} ${size}w`).join(', ');
  }

  const basePath = src.replace(/\.[^/.]+$/, '');
  return sizes.map(size => `${basePath}.${format}?w=${size} ${size}w`).join(', ');
}

/**
 * Preload critical images with modern format fallbacks
 */
export function preloadImage(
  src: string,
  options: {
    as?: 'image';
    type?: string;
    sizes?: string;
    fetchPriority?: 'high' | 'low' | 'auto';
  } = {}
) {
  if (typeof window === 'undefined') return;

  const link = document.createElement('link');
  link.rel = 'preload';
  link.href = src;
  link.as = options.as || 'image';

  if (options.type) {
    link.type = options.type;
  }

  if (options.sizes) {
    link.setAttribute('sizes', options.sizes);
  }

  if (options.fetchPriority) {
    link.setAttribute('fetchpriority', options.fetchPriority);
  }

  document.head.appendChild(link);
}

/**
 * Progressive image loading with intersection observer
 */
export class ProgressiveImageLoader {
  private observer: IntersectionObserver | null = null;

  constructor() {
    if (typeof window !== 'undefined' && 'IntersectionObserver' in window) {
      this.observer = new IntersectionObserver(
        entries => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              const img = entry.target as HTMLImageElement;
              this.loadImage(img);
              this.observer?.unobserve(img);
            }
          });
        },
        {
          rootMargin: '50px 0px',
          threshold: 0.01,
        }
      );
    }
  }

  observe(img: HTMLImageElement) {
    if (this.observer) {
      this.observer.observe(img);
    } else {
      // Fallback for browsers without IntersectionObserver
      this.loadImage(img);
    }
  }

  private async loadImage(img: HTMLImageElement) {
    const dataSrc = img.dataset.src;
    if (!dataSrc) return;

    try {
      // Check for modern format support
      const format = await getOptimalImageFormat();
      const optimizedSrc = this.getOptimizedSrc(dataSrc, format);

      // Create a new image to test loading
      const testImg = new Image();
      testImg.onload = () => {
        img.src = optimizedSrc;
        img.classList.add('loaded');
      };
      testImg.onerror = () => {
        // Fallback to original image
        img.src = dataSrc;
        img.classList.add('loaded');
      };
      testImg.src = optimizedSrc;
    } catch (error) {
      // Fallback to original image
      img.src = dataSrc;
      img.classList.add('loaded');
    }
  }

  private getOptimizedSrc(src: string, format: 'avif' | 'webp' | 'jpg'): string {
    if (format === 'jpg') return src;

    // Assume we have a service that generates optimized images
    const basePath = src.replace(/\.[^/.]+$/, '');
    return `${basePath}.${format}`;
  }

  disconnect() {
    if (this.observer) {
      this.observer.disconnect();
    }
  }
}

/**
 * Cache images in service worker for faster subsequent loads
 */
export function cacheImage(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if ('serviceWorker' in navigator && 'caches' in window) {
      caches.open('images-v1').then(cache => {
        cache.add(src).then(resolve).catch(reject);
      });
    } else {
      reject(new Error('Service Worker or Cache API not supported'));
    }
  });
}

/**
 * Lazy load image with modern format support
 */
export function lazyLoadImage(
  img: HTMLImageElement,
  src: string,
  options: {
    placeholder?: string;
    onLoad?: () => void;
    onError?: () => void;
  } = {}
) {
  const loader = new ProgressiveImageLoader();

  // Set placeholder
  if (options.placeholder) {
    img.src = options.placeholder;
  }

  // Set data-src for lazy loading
  img.dataset.src = src;

  // Add loading class
  img.classList.add('loading');

  // Set up event listeners
  img.addEventListener('load', () => {
    img.classList.remove('loading');
    options.onLoad?.();
  });

  img.addEventListener('error', () => {
    img.classList.remove('loading');
    options.onError?.();
  });

  // Start observing
  loader.observe(img);

  return loader;
}

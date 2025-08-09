import Image from 'next/image';
import { ComponentProps } from 'react';

interface OptimizedImageProps extends Omit<ComponentProps<typeof Image>, 'src' | 'alt'> {
  src: string;
  alt: string;
  priority?: boolean;
  sizes?: string;
  quality?: number;
}

/**
 * Optimized Image component with WebP/AVIF support and proper sizing
 *
 * Features:
 * - Automatic WebP/AVIF format support with fallbacks
 * - Responsive sizing with proper breakpoints
 * - Lazy loading by default (unless priority is set)
 * - Blur placeholder for smooth loading
 * - Optimized quality settings
 */
export default function OptimizedImage({
  src,
  alt,
  priority = false,
  sizes = '(max-width: 640px) 100vw, (max-width: 1200px) 50vw, 33vw',
  quality = 75,
  className = '',
  ...props
}: OptimizedImageProps) {
  return (
    <Image
      src={src}
      alt={alt}
      priority={priority}
      sizes={sizes}
      quality={quality}
      placeholder="blur"
      blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
      className={className}
      {...props}
    />
  );
}

/**
 * Hero Image component for above-the-fold images
 *
 * This component should be used for critical images that appear
 * above the fold and need to load immediately.
 */
export function HeroImage({
  src,
  alt,
  sizes = '100vw',
  quality = 85,
  className = '',
  ...props
}: OptimizedImageProps) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      priority={true}
      sizes={sizes}
      quality={quality}
      className={className}
      {...props}
    />
  );
}

/**
 * Avatar Image component for profile pictures
 *
 * Optimized for small, circular profile images with
 * appropriate sizing and quality settings.
 */
export function AvatarImage({
  src,
  alt,
  size = 40,
  quality = 75,
  className = '',
  ...props
}: OptimizedImageProps & { size?: number }) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      width={size}
      height={size}
      sizes={`${size}px`}
      quality={quality}
      className={`rounded-full ${className}`}
      {...props}
    />
  );
}

/**
 * Icon Image component for small decorative images
 *
 * Optimized for icons and small graphics with
 * higher quality and smaller sizes.
 */
export function IconImage({
  src,
  alt,
  size = 24,
  quality = 90,
  className = '',
  ...props
}: OptimizedImageProps & { size?: number }) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      width={size}
      height={size}
      sizes={`${size}px`}
      quality={quality}
      className={className}
      {...props}
    />
  );
}

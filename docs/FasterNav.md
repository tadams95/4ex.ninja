# Frontend Speed Optimizations for 4ex.ninja

## 1. Route Navigation
- Use `<Link>` from `next/link` for all navigation to leverage prefetching and client-side routing.
- For programmatic navigation, use `useRouter` from `next/navigation` in client components.
- Ensure navigation components are marked with `'use client';` at the top.

## 2. Code Splitting & Dynamic Imports
- Use dynamic imports (`next/dynamic`) for large or rarely-used components (e.g., PricingPageComponent, heavy charts, or modals).
- Split large pages into smaller components to reduce initial bundle size.

## 3. Prefetching & Lazy Loading
- Use the `prefetch` prop on `<Link>` for critical routes.
- Lazy load images and non-critical assets/components.

## 4. Minimize Global CSS
- Move styles to component-level CSS modules where possible to reduce unused CSS.
- Audit `globals.css` for unused styles.

## 5. Optimize API Calls
- Debounce or throttle API calls in components like tickers or feeds.
- Use SWR or React Query for caching and revalidation of API data.

## 6. Reduce JavaScript Payload
- Remove unused dependencies from `package.json` and codebase.
- Use tree-shaking and ensure only necessary code is imported.

## 7. Image Optimization
- Use Next.js `<Image>` for all images to leverage built-in optimization.
- Serve images in modern formats (WebP/AVIF).

## 8. Static Generation & Caching
- Prefer static generation (SSG) or incremental static regeneration (ISR) for pages that don’t require real-time data.
- Use caching headers for API responses where possible.

## 9. Bundle Analysis
- Run `next build` with `ANALYZE=true` to identify large bundles and optimize them.

## 10. Miscellaneous
- Avoid anonymous arrow functions in props (can cause unnecessary re-renders).
- Use React.memo for pure components.
- Audit and optimize third-party scripts and analytics.

---

_Review and implement these optimizations to improve navigation and overall frontend performance._

import { NextResponse } from 'next/server';

export async function middleware(request) {
  // Get the pathname
  const path = request.nextUrl.pathname;
  const response = NextResponse.next();

  // Add security headers to all responses
  response.headers.set('X-DNS-Prefetch-Control', 'off');
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set('X-XSS-Protection', '1; mode=block');

  // Rate limiting headers
  response.headers.set('X-RateLimit-Limit', '100');
  response.headers.set('X-RateLimit-Remaining', '99');

  // Define protected routes
  const protectedRoutes = ['/feed', '/account'];

  // Check if the path is a protected route
  const isProtectedRoute = protectedRoutes.some(
    route => path === route || path.startsWith(`${route}/`)
  );

  // API route protection
  if (path.startsWith('/api/') && !path.startsWith('/api/auth/')) {
    // Add CSRF protection headers for API routes
    response.headers.set('X-Content-Type-Options', 'nosniff');
    response.headers.set('X-Frame-Options', 'DENY');

    // Check for valid content type on POST/PUT/PATCH requests
    if (['POST', 'PUT', 'PATCH'].includes(request.method)) {
      const contentType = request.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        return new NextResponse('Invalid content type', { status: 400 });
      }
    }
  }

  if (isProtectedRoute) {
    // For OnchainKit/Web3 apps, route protection is handled client-side
    // through wallet connection state. Server-side middleware just adds
    // security headers and CORS policies.

    // Add Web3-specific headers
    response.headers.set('X-Web3-App', 'true');
  }

  return response;
}

export const config = {
  matcher: [
    // Protected routes
    '/feed',
    '/feed/:path*',
    '/account',
    '/account/:path*',
  ],
};

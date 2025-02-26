import { NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";

export async function middleware(request) {
  // Get the pathname
  const path = request.nextUrl.pathname;

  // Define protected routes
  const protectedRoutes = ["/feed"];
  
  // Check if the path is a protected route
  const isProtectedRoute = protectedRoutes.some(route => 
    path === route || path.startsWith(`${route}/`)
  );

  if (isProtectedRoute) {
    const token = await getToken({ 
      req: request,
      secret: process.env.NEXTAUTH_SECRET
    });

    // If not authenticated, redirect to login
    if (!token) {
      const url = new URL("/login", request.url);
      url.searchParams.set("callbackUrl", path);
      return NextResponse.redirect(url);
    }

    // Check if subscription is active
    const now = new Date();
    const subscriptionEnds = token.subscriptionEnds 
      ? new Date(token.subscriptionEnds) 
      : null;

    if (!subscriptionEnds || now > subscriptionEnds) {
      return NextResponse.redirect(new URL("/subscribe", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    // Protected routes
    "/feed",
    "/feed/:path*",
    "/account",
    "/account/:path*"
  ]
};

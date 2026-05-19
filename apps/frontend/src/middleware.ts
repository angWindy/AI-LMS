import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(_request: NextRequest) {
  // Allow all routes - auth handled client-side
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/courses/create",
    "/courses/my",
    "/users/:path*",
    "/profile/:path*",
    "/login",
    "/register",
  ],
};

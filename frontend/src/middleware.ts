import { type NextRequest, NextResponse } from "next/server";

const PROTECTED = [
  "/dashboard",
  "/profile",
  "/ai-chat",
  "/services",
  "/schemes",
  "/search",
  "/bookmarks",
  "/notifications",
  "/settings",
];

const ADMIN_ONLY = ["/admin"];

const PUBLIC_AUTH = ["/login", "/register", "/verify-otp", "/forgot-password"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const isLoggedIn = request.cookies.has("onegov-logged-in");
  const isAdmin = request.cookies.get("onegov-role")?.value === "admin";

  // Logged-in users visiting auth pages redirect to appropriate landing page
  if (isLoggedIn && PUBLIC_AUTH.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
    const target = isAdmin ? "/admin" : "/dashboard";
    return NextResponse.redirect(new URL(target, request.url));
  }

  // Admin-only routes
  if (ADMIN_ONLY.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
    if (!isLoggedIn) {
      const url = new URL("/login", request.url);
      url.searchParams.set("redirect", pathname);
      return NextResponse.redirect(url);
    }
    if (!isAdmin) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
  }

  // Protected user routes
  if (PROTECTED.some((p) => pathname === p || pathname.startsWith(`${p}/`)) && !isLoggedIn) {
    const url = new URL("/login", request.url);
    url.searchParams.set("redirect", pathname);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api/|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"],
};


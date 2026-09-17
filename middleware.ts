import { NextRequest, NextResponse } from "next/server";
import { jwtVerify } from "jose";

const COOKIE_NAME = "gyan_session";

async function isAuthed(req: NextRequest): Promise<boolean> {
  const token = req.cookies.get(COOKIE_NAME)?.value;
  if (!token) return false;
  const secret = process.env.SESSION_SECRET;
  if (!secret) return false;
  try {
    await jwtVerify(token, new TextEncoder().encode(secret));
    return true;
  } catch {
    return false;
  }
}

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const authed = await isAuthed(req);

  if (pathname.startsWith("/chat") && !authed) {
    return NextResponse.redirect(new URL("/login", req.url));
  }
  if (pathname === "/login" && authed) {
    return NextResponse.redirect(new URL("/chat", req.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/chat/:path*", "/login"],
};

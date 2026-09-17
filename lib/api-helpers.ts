import { NextResponse } from "next/server";

/**
 * Turns any thrown error into a proper JSON response instead of letting
 * Next.js send back an empty/HTML error page, which is what was causing
 * "Failed to execute 'json' on 'Response': Unexpected end of JSON input"
 * on the client - the client tried to .json() a body that wasn't JSON.
 */
export function jsonError(err: unknown, fallback = "Something went wrong.") {
  console.error(err);
  const message = err instanceof Error ? err.message : fallback;
  return NextResponse.json({ error: message }, { status: 500 });
}

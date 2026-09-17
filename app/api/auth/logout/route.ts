import { NextResponse } from "next/server";
import { destroySession } from "@/lib/auth";
import { jsonError } from "@/lib/api-helpers";

export const dynamic = "force-dynamic";

export async function POST() {
  try {
    await destroySession();
    return NextResponse.json({ ok: true });
  } catch (err) {
    return jsonError(err, "Could not log you out.");
  }
}

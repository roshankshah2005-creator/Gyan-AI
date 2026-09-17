import { NextRequest, NextResponse } from "next/server";
import { verifyUser, listChats, createChat } from "@/lib/db";
import { createSession } from "@/lib/auth";
import { jsonError } from "@/lib/api-helpers";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  try {
    const { email, password } = await req.json();
    const cleanEmail = (email ?? "").trim().toLowerCase();
    const cleanPassword = (password ?? "").trim();

    const name = await verifyUser(cleanEmail, cleanPassword);
    if (!name) {
      return NextResponse.json({ error: "Invalid email or password." }, { status: 401 });
    }

    const chats = await listChats(cleanEmail);
    if (chats.length === 0) await createChat(cleanEmail);

    await createSession(cleanEmail);
    return NextResponse.json({ ok: true });
  } catch (err) {
    return jsonError(err, "Could not log you in.");
  }
}

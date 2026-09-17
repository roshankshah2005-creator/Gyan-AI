import { NextRequest, NextResponse } from "next/server";
import { getSessionEmail } from "@/lib/auth";
import { getChat, deleteChat } from "@/lib/db";
import { jsonError } from "@/lib/api-helpers";

export const dynamic = "force-dynamic";

export async function GET(_req: NextRequest, { params }: { params: { id: string } }) {
  try {
    const email = await getSessionEmail();
    if (!email) return NextResponse.json({ error: "Not authenticated" }, { status: 401 });

    const chat = await getChat(Number(params.id), email);
    if (!chat) return NextResponse.json({ error: "Not found" }, { status: 404 });
    return NextResponse.json({ chat });
  } catch (err) {
    return jsonError(err, "Could not load this chat.");
  }
}

export async function DELETE(_req: NextRequest, { params }: { params: { id: string } }) {
  try {
    const email = await getSessionEmail();
    if (!email) return NextResponse.json({ error: "Not authenticated" }, { status: 401 });

    await deleteChat(Number(params.id), email);
    return NextResponse.json({ ok: true });
  } catch (err) {
    return jsonError(err, "Could not delete this chat.");
  }
}

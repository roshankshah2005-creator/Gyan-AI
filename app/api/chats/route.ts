import { NextResponse } from "next/server";
import { getSessionEmail } from "@/lib/auth";
import { listChats, createChat, getUser } from "@/lib/db";
import { jsonError } from "@/lib/api-helpers";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const email = await getSessionEmail();
    if (!email) return NextResponse.json({ error: "Not authenticated" }, { status: 401 });

    const [chats, user] = await Promise.all([listChats(email), getUser(email)]);
    return NextResponse.json({ chats, userName: user?.name ?? "" });
  } catch (err) {
    return jsonError(err, "Could not load your chats.");
  }
}

export async function POST() {
  try {
    const email = await getSessionEmail();
    if (!email) return NextResponse.json({ error: "Not authenticated" }, { status: 401 });

    const id = await createChat(email);
    return NextResponse.json({ id });
  } catch (err) {
    return jsonError(err, "Could not create a new chat.");
  }
}

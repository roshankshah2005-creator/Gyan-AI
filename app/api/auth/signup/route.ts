import { NextRequest, NextResponse } from "next/server";
import { registerUser, createChat } from "@/lib/db";
import { createSession } from "@/lib/auth";
import { jsonError } from "@/lib/api-helpers";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  try {
    const { name, email, password } = await req.json();

    if (!name?.trim() || !email?.trim() || !password?.trim()) {
      return NextResponse.json({ error: "Please fill in all fields." }, { status: 400 });
    }

    const cleanEmail = email.trim().toLowerCase();
    const ok = await registerUser(cleanEmail, name.trim(), password.trim());
    if (!ok) {
      return NextResponse.json(
        { error: "Email is already registered! Please switch to Log In." },
        { status: 409 }
      );
    }

    await createChat(cleanEmail);
    await createSession(cleanEmail);

    return NextResponse.json({ ok: true });
  } catch (err) {
    return jsonError(err, "Could not create your account.");
  }
}

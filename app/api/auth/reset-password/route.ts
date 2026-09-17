import { NextRequest, NextResponse } from "next/server";
import { getUser, updatePassword } from "@/lib/db";
import { jsonError } from "@/lib/api-helpers";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  try {
    const { email, newPassword } = await req.json();
    const cleanEmail = (email ?? "").trim().toLowerCase();
    const cleanPassword = (newPassword ?? "").trim();

    if (!cleanEmail || !cleanPassword) {
      return NextResponse.json({ error: "Please fill in both fields." }, { status: 400 });
    }

    const user = await getUser(cleanEmail);
    if (!user) {
      return NextResponse.json(
        { error: "No account found with this email address." },
        { status: 404 }
      );
    }

    await updatePassword(cleanEmail, cleanPassword);
    return NextResponse.json({ ok: true });
  } catch (err) {
    return jsonError(err, "Could not reset your password.");
  }
}

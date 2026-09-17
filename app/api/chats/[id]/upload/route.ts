import { NextRequest, NextResponse } from "next/server";
import { getSessionEmail } from "@/lib/auth";
import { getChat, saveChat } from "@/lib/db";
import { chunkText } from "@/lib/rag";
import { jsonError } from "@/lib/api-helpers";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(req: NextRequest, { params }: { params: { id: string } }) {
  try {
    const email = await getSessionEmail();
    if (!email) return NextResponse.json({ error: "Not authenticated" }, { status: 401 });

    const chatId = Number(params.id);
    const chat = await getChat(chatId, email);
    if (!chat) return NextResponse.json({ error: "Chat not found" }, { status: 404 });

    const formData = await req.formData();
    const file = formData.get("file") as File | null;
    if (!file) return NextResponse.json({ error: "No file provided" }, { status: 400 });

    let rawText = "";
    try {
      if (file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")) {
        const buffer = Buffer.from(await file.arrayBuffer());
        const pdfParse = (await import("pdf-parse")).default;
        const parsed = await pdfParse(buffer);
        rawText = parsed.text || "";
      } else {
        rawText = await file.text();
      }
    } catch (err: any) {
      return NextResponse.json({ error: `Error reading file: ${err.message}` }, { status: 400 });
    }

    if (!rawText.trim()) {
      return NextResponse.json(
        { error: "Could not extract text. Make sure your PDF has selectable text." },
        { status: 400 }
      );
    }

    const chunks = chunkText(rawText);
    const document = { filename: file.name, chunks };

    await saveChat(chatId, email, chat.title, chat.messages, document);
    return NextResponse.json({ document });
  } catch (err) {
    return jsonError(err, "Could not process this document.");
  }
}

export async function DELETE(_req: NextRequest, { params }: { params: { id: string } }) {
  try {
    const email = await getSessionEmail();
    if (!email) return NextResponse.json({ error: "Not authenticated" }, { status: 401 });

    const chatId = Number(params.id);
    const chat = await getChat(chatId, email);
    if (!chat) return NextResponse.json({ error: "Chat not found" }, { status: 404 });

    await saveChat(chatId, email, chat.title, chat.messages, null);
    return NextResponse.json({ ok: true });
  } catch (err) {
    return jsonError(err, "Could not remove the document.");
  }
}

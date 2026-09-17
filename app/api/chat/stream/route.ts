import { NextRequest, NextResponse } from "next/server";
import Groq from "groq-sdk";
import { getSessionEmail } from "@/lib/auth";
import { getChat, saveChat, ChatMessage } from "@/lib/db";
import { retrieveRelevantChunks } from "@/lib/rag";
import { SYSTEM_PROMPTS, Persona } from "@/lib/personas";
import { jsonError } from "@/lib/api-helpers";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const MODEL = "openai/gpt-oss-20b";

export async function POST(req: NextRequest) {
  let email: string | null;
  let chatId: number, prompt: string, persona: Persona;
  let chat;
  let groq: Groq;

  try {
    email = await getSessionEmail();
    if (!email) return NextResponse.json({ error: "Not authenticated" }, { status: 401 });

    const groqApiKey = process.env.GROQ_API_KEY;
    if (!groqApiKey) {
      return NextResponse.json({ error: "Groq API key is missing on the server." }, { status: 500 });
    }

    ({ chatId, prompt, persona } = (await req.json()) as {
      chatId: number;
      prompt: string;
      persona: Persona;
    });

    chat = await getChat(chatId, email);
    if (!chat) return NextResponse.json({ error: "Chat not found" }, { status: 404 });

    groq = new Groq({ apiKey: groqApiKey });
  } catch (err) {
    return jsonError(err, "Could not start the chat.");
  }

  const userMessage: ChatMessage = { role: "user", content: prompt };
  const messages = [...chat.messages, userMessage];

  // Auto-generate a short title for brand-new chats, same as the original app.
  let title = chat.title;
  if (title === "New Conversation") {
    try {
      const titleRes = await groq.chat.completions.create({
        model: MODEL,
        messages: [
          {
            role: "system",
            content: "Generate a short title (max 4 words) summarizing this query. No quotes, no punctuation.",
          },
          { role: "user", content: prompt },
        ],
        max_tokens: 15,
      });
      const generated = titleRes.choices[0]?.message?.content?.trim();
      title = generated || (prompt.length > 25 ? prompt.slice(0, 25) + "..." : prompt);
    } catch {
      title = prompt.length > 25 ? prompt.slice(0, 25) + "..." : prompt;
    }
  }

  const basePrompt = SYSTEM_PROMPTS[persona] ?? SYSTEM_PROMPTS["General Companion"];
  let systemContent = basePrompt;
  if (chat.document?.chunks?.length) {
    const ragContext = retrieveRelevantChunks(prompt, chat.document.chunks, 6);
    if (ragContext) {
      systemContent = `${basePrompt}\n\n[CONTEXT KNOWLEDGE BASE]\nUse the following extracted document text to answer the user's question accurately and thoroughly:\n${ragContext}`;
    }
  }

  const formattedMessages = [
    { role: "system" as const, content: systemContent },
    ...messages.map((m) => ({ role: m.role, content: m.content })),
  ];

  const encoder = new TextEncoder();
  let fullResponse = "";

  const stream = new ReadableStream({
    async start(controller) {
      try {
        const completion = await groq.chat.completions.create({
          model: MODEL,
          messages: formattedMessages,
          temperature: 0.5,
          max_tokens: 2048,
          stream: true,
        });

        for await (const chunk of completion) {
          const delta = chunk.choices[0]?.delta?.content;
          if (delta) {
            fullResponse += delta;
            controller.enqueue(encoder.encode(delta));
          }
        }
      } catch (err: any) {
        const errMsg = `AI Error: ${err.message}`;
        fullResponse = errMsg;
        controller.enqueue(encoder.encode(errMsg));
      } finally {
        const finalMessages: ChatMessage[] = [
          ...messages,
          { role: "assistant", content: fullResponse },
        ];
        await saveChat(chatId, email, title, finalMessages, chat.document);
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "X-Chat-Title": encodeURIComponent(title),
    },
  });
}

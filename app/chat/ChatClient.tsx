"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { PERSONAS, Persona } from "@/lib/personas";

type ChatMessage = { role: "user" | "assistant"; content: string };
type ChatDocument = { filename: string; chunks: string[] } | null;
type Chat = {
  id: number;
  title: string;
  messages: ChatMessage[];
  document: ChatDocument;
};

export default function ChatClient() {
  const router = useRouter();
  const [userName, setUserName] = useState("");
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<number | null>(null);
  const [persona, setPersona] = useState<Persona>("General Companion");
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const currentChat = chats.find((c) => c.id === currentChatId) ?? null;

  useEffect(() => {
    loadChats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [currentChat?.messages.length, sending]);

  async function loadChats(selectId?: number) {
    const res = await fetch("/api/chats");
    if (!res.ok) return;
    const data = await res.json();
    setUserName(data.userName);
    setChats(data.chats);
    if (data.chats.length > 0) {
      setCurrentChatId(selectId ?? data.chats[0].id);
    }
  }

  async function handleNewChat() {
    const res = await fetch("/api/chats", { method: "POST" });
    const data = await res.json();
    await loadChats(data.id);
  }

  async function handleDeleteChat(id: number) {
    await fetch(`/api/chats/${id}`, { method: "DELETE" });
    await loadChats();
  }

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !currentChat) return;
    setUploading(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`/api/chats/${currentChat.id}/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      setChats((prev) =>
        prev.map((c) => (c.id === currentChat.id ? { ...c, document: data.document } : c))
      );
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleRemoveDocument() {
    if (!currentChat) return;
    await fetch(`/api/chats/${currentChat.id}/upload`, { method: "DELETE" });
    setChats((prev) =>
      prev.map((c) => (c.id === currentChat.id ? { ...c, document: null } : c))
    );
  }

  async function handleSend() {
    if (!input.trim() || !currentChat || sending) return;
    const prompt = input.trim();
    setInput("");
    setSending(true);
    setError("");

    const chatId = currentChat.id;
    // optimistic user message
    setChats((prev) =>
      prev.map((c) =>
        c.id === chatId
          ? { ...c, messages: [...c.messages, { role: "user", content: prompt }] }
          : c
      )
    );
    // placeholder assistant message we will fill in as tokens arrive
    setChats((prev) =>
      prev.map((c) =>
        c.id === chatId
          ? { ...c, messages: [...c.messages, { role: "assistant", content: "" }] }
          : c
      )
    );

    try {
      const res = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chatId, prompt, persona }),
      });
      if (!res.ok || !res.body) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || "Something went wrong.");
      }

      const newTitle = res.headers.get("X-Chat-Title");
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let acc = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        acc += decoder.decode(value, { stream: true });
        setChats((prev) =>
          prev.map((c) => {
            if (c.id !== chatId) return c;
            const msgs = [...c.messages];
            msgs[msgs.length - 1] = { role: "assistant", content: acc };
            return { ...c, messages: msgs };
          })
        );
      }

      if (newTitle) {
        const decodedTitle = decodeURIComponent(newTitle);
        setChats((prev) =>
          prev.map((c) => (c.id === chatId ? { ...c, title: decodedTitle } : c))
        );
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  }

  if (!currentChat) {
    return <div className="auth-wrap">Loading...</div>;
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-logo">GYAN</div>
        <div style={{ fontSize: 13, color: "#94a3b8" }}>
          Logged in as: <strong style={{ color: "#e2e8f0" }}>{userName}</strong>
        </div>
        <hr />

        <div>
          <h3>AI Persona</h3>
          <select value={persona} onChange={(e) => setPersona(e.target.value as Persona)}>
            {PERSONAS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>

        <button className="btn" onClick={handleNewChat}>
          + New Chat
        </button>

        <div>
          <h3>📚 Knowledge Base Document</h3>
          {currentChat.document ? (
            <div className="doc-badge">
              <span>• {currentChat.document.filename}</span>
              <button onClick={handleRemoveDocument} title="Remove document">
                🗑️
              </button>
            </div>
          ) : (
            <div className="upload-row">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt"
                onChange={handleUpload}
                disabled={uploading}
              />
            </div>
          )}
          {uploading && <div style={{ fontSize: 12, color: "#94a3b8" }}>Processing document...</div>}
        </div>

        <div style={{ flex: 1, overflowY: "auto" }}>
          <h3>Chat History</h3>
          {chats.map((chat) => (
            <div className="chat-list-item" key={chat.id}>
              <button
                className={`title ${chat.id === currentChatId ? "active" : ""}`}
                onClick={() => setCurrentChatId(chat.id)}
              >
                {chat.title}
              </button>
              <button className="del" onClick={() => handleDeleteChat(chat.id)} title="Delete chat">
                ❌
              </button>
            </div>
          ))}
        </div>

        <hr />
        <button className="btn btn-secondary" onClick={handleLogout}>
          Log Out
        </button>
      </aside>

      <main className="main-col">
        {currentChat.messages.length === 0 ? (
          <div className="empty-state">How can I help you, {userName}!!</div>
        ) : (
          <div className="messages">
            {currentChat.messages.map((m, i) => (
              <div key={i} className={`msg ${m.role}`}>
                {m.content}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}

        {error && <div className="error-msg" style={{ padding: "0 24px" }}>{error}</div>}

        <div className="chat-input-bar">
          <input
            placeholder="Ask anything or query your uploaded document..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            disabled={sending}
          />
          <button onClick={handleSend} disabled={sending || !input.trim()}>
            {sending ? "..." : "Send"}
          </button>
        </div>
      </main>
    </div>
  );
}

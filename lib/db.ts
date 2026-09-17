import { Pool } from "pg";
import bcrypt from "bcryptjs";

// Works with any managed Postgres (Neon, Supabase, Vercel Marketplace Postgres, etc).
// Set DATABASE_URL (or POSTGRES_URL) to your connection string.
const connectionString = process.env.DATABASE_URL || process.env.POSTGRES_URL;

declare global {
  // eslint-disable-next-line no-var
  var _gyanPgPool: Pool | undefined;
}

function getPool() {
  if (!connectionString) {
    throw new Error("DATABASE_URL (or POSTGRES_URL) env var is not set");
  }
  if (!global._gyanPgPool) {
    global._gyanPgPool = new Pool({
      connectionString,
      ssl: connectionString.includes("localhost") ? false : { rejectUnauthorized: false },
    });
  }
  return global._gyanPgPool;
}

export type ChatMessage = { role: "user" | "assistant"; content: string };
export type ChatDocument = { filename: string; chunks: string[] } | null;
export type Chat = {
  id: number;
  title: string;
  messages: ChatMessage[];
  document: ChatDocument;
};

export async function getUser(email: string) {
  const { rows } = await getPool().query(
    "SELECT email, name FROM users WHERE email = $1",
    [email]
  );
  return rows[0] as { email: string; name: string } | undefined;
}

export async function registerUser(email: string, name: string, password: string) {
  const pool = getPool();
  const existing = await pool.query("SELECT email FROM users WHERE email = $1", [email]);
  if (existing.rows.length > 0) return false;
  const hash = await bcrypt.hash(password, 10);
  await pool.query(
    "INSERT INTO users (email, name, password_hash) VALUES ($1, $2, $3)",
    [email, name, hash]
  );
  return true;
}

export async function verifyUser(email: string, password: string) {
  const { rows } = await getPool().query(
    "SELECT name, password_hash FROM users WHERE email = $1",
    [email]
  );
  const row = rows[0];
  if (!row) return null;
  const ok = await bcrypt.compare(password, row.password_hash as string);
  return ok ? (row.name as string) : null;
}

export async function updatePassword(email: string, newPassword: string) {
  const hash = await bcrypt.hash(newPassword, 10);
  await getPool().query("UPDATE users SET password_hash = $1 WHERE email = $2", [hash, email]);
}

export async function listChats(email: string): Promise<Chat[]> {
  const { rows } = await getPool().query(
    `SELECT id, title, messages, document FROM chats
     WHERE email = $1
     ORDER BY updated_at DESC`,
    [email]
  );
  return rows.map((r) => ({
    id: r.id as number,
    title: r.title as string,
    messages: (r.messages as ChatMessage[]) ?? [],
    document: (r.document as ChatDocument) ?? null,
  }));
}

export async function createChat(email: string): Promise<number> {
  const { rows } = await getPool().query(
    `INSERT INTO chats (email, title, messages, document)
     VALUES ($1, 'New Conversation', '[]'::jsonb, NULL)
     RETURNING id`,
    [email]
  );
  return rows[0].id as number;
}

export async function getChat(id: number, email: string): Promise<Chat | undefined> {
  const { rows } = await getPool().query(
    "SELECT id, title, messages, document FROM chats WHERE id = $1 AND email = $2",
    [id, email]
  );
  const r = rows[0];
  if (!r) return undefined;
  return {
    id: r.id as number,
    title: r.title as string,
    messages: (r.messages as ChatMessage[]) ?? [],
    document: (r.document as ChatDocument) ?? null,
  };
}

export async function saveChat(
  id: number,
  email: string,
  title: string,
  messages: ChatMessage[],
  document: ChatDocument
) {
  await getPool().query(
    `UPDATE chats
     SET title = $1,
         messages = $2::jsonb,
         document = $3::jsonb,
         updated_at = now()
     WHERE id = $4 AND email = $5`,
    [title, JSON.stringify(messages), document ? JSON.stringify(document) : null, id, email]
  );
}

export async function deleteChat(id: number, email: string) {
  await getPool().query("DELETE FROM chats WHERE id = $1 AND email = $2", [id, email]);
}

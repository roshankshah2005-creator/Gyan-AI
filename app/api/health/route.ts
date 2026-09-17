import { NextResponse } from "next/server";
import { Pool } from "pg";

export const dynamic = "force-dynamic";

export async function GET() {
  const checks: Record<string, string> = {
    GROQ_API_KEY: process.env.GROQ_API_KEY ? "set" : "MISSING",
    SESSION_SECRET: process.env.SESSION_SECRET ? "set" : "MISSING",
    DATABASE_URL: process.env.DATABASE_URL || process.env.POSTGRES_URL ? "set" : "MISSING",
  };

  let db = "not tested";
  const connectionString = process.env.DATABASE_URL || process.env.POSTGRES_URL;
  if (connectionString) {
    const pool = new Pool({
      connectionString,
      ssl: connectionString.includes("localhost") ? false : { rejectUnauthorized: false },
    });
    try {
      await pool.query("SELECT 1");
      const tables = await pool.query(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
      );
      const names = tables.rows.map((r) => r.table_name);
      db = `connected. tables found: ${names.join(", ") || "NONE - run 'npm run init-db'"}`;
    } catch (err: any) {
      db = `connection FAILED: ${err.message}`;
    } finally {
      await pool.end();
    }
  }

  return NextResponse.json({ env: checks, database: db });
}

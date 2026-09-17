// Run once after you set DATABASE_URL to your Postgres connection string:
//   npm run init-db
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import path from "path";
import pg from "pg";

const connectionString = process.env.DATABASE_URL || process.env.POSTGRES_URL;
if (!connectionString) {
  console.error("Set DATABASE_URL (or POSTGRES_URL) before running this script.");
  process.exit(1);
}

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const schema = readFileSync(path.join(__dirname, "../db/schema.sql"), "utf-8");

const pool = new pg.Pool({
  connectionString,
  ssl: connectionString.includes("localhost") ? false : { rejectUnauthorized: false },
});

await pool.query(schema);
console.log("✅ Database schema created.");
await pool.end();

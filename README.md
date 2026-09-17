# GYAN AI — Vercel + Postgres rewrite

This is a rewrite of the original Streamlit/Python app as a **Next.js** app so
it can actually run on Vercel. The important thing to understand: Vercel is
serverless — there's no persistent disk between requests — so the original
`sqlite3` file (`gyan_ai.db`) can never work there. User accounts and chat
history are now stored in **Postgres** instead.

What was ported over, 1:1 in behavior:
- Sign up / log in / forgot password (math captcha was dropped — see note below)
- Multiple AI personas (same system prompts)
- Streaming responses from Groq
- Saved chat history per user, with rename-by-first-message like the original
- Single-document upload (PDF/TXT) + retrieval-augmented answers. The Python
  version used scikit-learn's `TfidfVectorizer` + cosine similarity — `lib/rag.ts`
  reimplements the same idea (term-frequency vectors + cosine similarity) in
  plain TypeScript so there's no numpy/sklearn dependency to worry about on Vercel.

## 1. Local setup

```bash
npm install
cp .env.example .env.local
```

Fill in `.env.local`:
- `GROQ_API_KEY` — from https://console.groq.com/keys
- `SESSION_SECRET` — any long random string (`openssl rand -base64 32`)
- `DATABASE_URL` — a Postgres connection string (see step 2)

## 2. Get a Postgres database

The app talks to Postgres through the plain `pg` driver, so **any** Postgres
provider works — just put its connection string in `DATABASE_URL`. No code
changes needed either way.

### Option A: Supabase (recommended — generous free tier, simple dashboard)
1. Create a project at https://supabase.com/dashboard
2. Project Settings → Database → **Connection string** → copy the "URI" one
   (use the **Connection pooling** string, port `6543`, if you're deploying
   to Vercel — serverless functions open a lot of short-lived connections,
   and the pooler handles that much better than a direct connection).
3. Put it in `DATABASE_URL`. It already includes `?sslmode=require` — keep that.

### Option B: Vercel's own Postgres marketplace
In the Vercel dashboard, open your project → **Storage** → **Marketplace
Database Providers** → add a **Postgres** (Neon is the default option).
Vercel injects the connection string as an env var automatically once it's
attached. Copy that same value into `DATABASE_URL` in `.env.local` for local
dev (or run `npx vercel env pull .env.local`).

Railway, Neon directly, RDS, etc. all work the same way — just the connection
string changes.

### Then, either way, create the tables once
```bash
npm run init-db
```
This is the step people most often forget — if you skip it, sign-up will
fail with a "relation users does not exist" error (see troubleshooting below).

## 3. Run it locally

```bash
npm run dev
```

Visit http://localhost:3000.

## 4. Deploy to Vercel

```bash
npx vercel
```

or connect the GitHub repo in the Vercel dashboard. Either way, set these
three Project → Settings → Environment Variables (Production **and**
Preview): `GROQ_API_KEY`, `SESSION_SECRET`, `DATABASE_URL` (auto-set if you
attached the database through the Storage tab). Then run `npm run init-db`
once against the production database (or point `DATABASE_URL` locally at it
and run the script) to create the tables.

## Troubleshooting

**"Failed to execute 'json' on 'Response': Unexpected end of JSON input"**
means an API route crashed *before* it could send a response body back — the
browser tried to parse an empty one. Every route now wraps its logic in
try/catch (`lib/api-helpers.ts`) so this specific symptom shouldn't recur;
you'll get a real error message in the sign-up form instead. If you deployed
before pulling this update, the underlying cause was almost always one of:

1. **`DATABASE_URL` not set** in the Vercel project's environment variables.
2. **`SESSION_SECRET` not set.**
3. **Tables never created** — `npm run init-db` wasn't run against the
   production database.

Visit **`/api/health`** on your deployed site (e.g.
`https://your-app.vercel.app/api/health`) to check all three at once — it
reports which env vars are set and whether it can actually connect to the
database and see the `users`/`chats` tables. Fix whatever it flags, redeploy
if you changed env vars (Vercel requires a redeploy to pick up new ones), and
try signing up again. Remove or protect this route once everything works, since
it reports which env vars are configured.

## Notes / things that changed from the original

- **Passwords are now hashed** with bcrypt before being stored, instead of
  being kept as plain text in the database — worth keeping even though it's
  more code, since a leaked users table would otherwise expose every password.
- **The math captcha was dropped.** It's easy for any script to solve, so it
  mainly filtered accidental bot traffic, not deliberate abuse. If you want
  real bot protection on sign-up, add Cloudflare Turnstile or hCaptcha to the
  `/login` form and verify the token server-side in `app/api/auth/signup/route.ts`.
- **Password reset has no email verification step** (same as the original —
  anyone who knows an email can reset that account's password). Fine for a
  personal/demo project; for anything with real users you'd want to email a
  reset link/token instead of resetting inline.
- Sessions are a signed JWT in an httpOnly cookie (`middleware.ts` guards
  `/chat`), rather than Streamlit's server-side session state.

## Project structure

```
app/
  login/page.tsx           – sign up / log in / forgot password UI
  chat/page.tsx + ChatClient.tsx  – main chat UI (sidebar, personas, upload)
  api/auth/...              – signup, login, logout, reset-password
  api/chats/...              – list/create/get/delete chats, document upload
  api/chat/stream/route.ts  – streams the Groq completion, saves to DB
lib/
  db.ts        – all Postgres queries
  auth.ts      – session cookie helpers
  rag.ts       – chunking + cosine-similarity retrieval
  personas.ts  – persona system prompts
db/schema.sql  – table definitions
scripts/init-db.mjs – one-time setup script
```

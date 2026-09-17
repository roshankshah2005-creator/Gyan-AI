"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

type Mode = "login" | "signup" | "forgot";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);
    try {
      if (mode === "login") {
        const res = await fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Login failed");
        router.push("/chat");
        router.refresh();
      } else if (mode === "signup") {
        const res = await fetch("/api/auth/signup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, email, password }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Sign up failed");
        router.push("/chat");
        router.refresh();
      } else {
        const res = await fetch("/api/auth/reset-password", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, newPassword }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Reset failed");
        setSuccess("Password updated! You can log in now.");
        setMode("login");
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <h1 className="brand-logo" style={{ textAlign: "center", display: "block" }}>
          GYAN
        </h1>
        <p className="sub">Welcome to GYAN</p>

        {mode !== "forgot" && (
          <div className="mode-toggle">
            <button
              type="button"
              className={mode === "login" ? "active" : ""}
              onClick={() => {
                setMode("login");
                setError("");
              }}
            >
              Log In
            </button>
            <button
              type="button"
              className={mode === "signup" ? "active" : ""}
              onClick={() => {
                setMode("signup");
                setError("");
              }}
            >
              Sign Up
            </button>
          </div>
        )}

        <form onSubmit={submit}>
          {mode === "signup" && (
            <div className="field">
              <label>Your Name</label>
              <input value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
          )}

          <div className="field">
            <label>Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          {mode === "forgot" ? (
            <div className="field">
              <label>New Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
            </div>
          ) : (
            <div className="field">
              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          )}

          {error && <div className="error-msg">{error}</div>}
          {success && <div className="success-msg">{success}</div>}

          <button className="btn" disabled={loading} type="submit">
            {loading
              ? "Please wait..."
              : mode === "login"
              ? "Log In"
              : mode === "signup"
              ? "Sign Up"
              : "Update Password"}
          </button>
        </form>

        {mode === "login" && (
          <button className="link-btn" onClick={() => setMode("forgot")}>
            Forgot Password?
          </button>
        )}
        {mode === "forgot" && (
          <button className="link-btn" onClick={() => setMode("login")}>
            Back to Log In
          </button>
        )}
      </div>
    </div>
  );
}

import { FileSearch, LockKeyhole, ShieldCheck } from "lucide-react";
import React, { useState } from "react";

import { useAuth } from "../context/AuthContext";

export function LoginPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      if (mode === "register") {
        await register(form);
      } else {
        await login({ email: form.email, password: form.password });
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen bg-slate-950 text-white lg:grid-cols-[1.1fr_0.9fr]">
      <section className="flex min-h-[360px] flex-col justify-between border-b border-white/10 p-6 sm:p-10 lg:border-b-0 lg:border-r">
        <div className="flex items-center gap-3">
          <div className="rounded-md bg-white/10 p-3 text-cyan-200">
            <FileSearch className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl font-semibold">Financial Document Analyser</h1>
            <p className="text-sm text-slate-300">Secure AI analysis for financial PDFs.</p>
          </div>
        </div>

        <div className="max-w-2xl">
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-200">Private document intelligence</p>
          <h2 className="mt-3 text-4xl font-semibold leading-tight sm:text-5xl">Turn dense PDFs into cited answers.</h2>
          <p className="mt-4 max-w-xl text-base leading-7 text-slate-300">
            Upload financial documents, search across them with AI, and inspect the exact source text behind every answer.
          </p>
        </div>

        <div className="grid gap-3 text-sm text-slate-200 sm:grid-cols-2">
          <div className="rounded-lg border border-white/10 bg-white/5 p-4">
            <ShieldCheck className="mb-3 h-5 w-5 text-emerald-300" />
            Cited retrieval across uploaded files
          </div>
          <div className="rounded-lg border border-white/10 bg-white/5 p-4">
            <LockKeyhole className="mb-3 h-5 w-5 text-cyan-200" />
            Password-protected workspace
          </div>
        </div>
      </section>

      <section className="flex items-center justify-center bg-slate-50 p-6 text-ink">
        <div className="w-full max-w-md rounded-lg border border-line bg-white p-6 shadow-soft">
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-ink">{mode === "register" ? "Create your workspace" : "Welcome back"}</h2>
            <p className="text-sm text-muted">Sign in to upload documents and ask grounded questions.</p>
          </div>

        <div className="mb-5 grid grid-cols-2 rounded-md bg-gray-100 p-1">
          <button className={`rounded px-3 py-2 text-sm font-medium ${mode === "login" ? "bg-white text-ink shadow-sm" : "text-muted"}`} onClick={() => setMode("login")}>
            Login
          </button>
          <button className={`rounded px-3 py-2 text-sm font-medium ${mode === "register" ? "bg-white text-ink shadow-sm" : "text-muted"}`} onClick={() => setMode("register")}>
            Register
          </button>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          {mode === "register" && (
            <label className="block">
              <span className="text-sm font-medium text-ink">Name</span>
              <input
                className="mt-1 w-full rounded-md border border-line px-3 py-2 outline-none focus:border-brand"
                required
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
              />
            </label>
          )}
          <label className="block">
            <span className="text-sm font-medium text-ink">Email</span>
            <input
              className="mt-1 w-full rounded-md border border-line px-3 py-2 outline-none focus:border-brand"
              required
              type="email"
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-ink">Password</span>
            <input
              className="mt-1 w-full rounded-md border border-line px-3 py-2 outline-none focus:border-brand"
              required
              minLength={8}
              type="password"
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
            />
          </label>

          {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>}

          <button className="w-full rounded-md bg-brand px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-60" disabled={loading}>
            {loading ? "Please wait..." : mode === "register" ? "Create account" : "Login"}
          </button>
        </form>
        </div>
      </section>
    </main>
  );
}

// ---------------------------------------------------------------------------
// Login.jsx (Phase 9)
// ---------------------------------------------------------------------------
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion } from "motion/react";
import { LogIn, Mail, Lock, AlertCircle, ShieldCheck } from "lucide-react";

import { useAuth } from "../context/AuthContext";
import { buttonVariants } from "../lib/utils";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      const user = await login(email.trim(), password);
      // Route by role; honour a "from" if it suits the role.
      if (user.role === "student") {
        const from = location.state?.from;
        navigate(from && from.startsWith("/student") ? from : "/track", { replace: true });
      } else {
        navigate("/admin", { replace: true });
      }
    } catch (err) {
      setError(err.message || "Login failed. Please check your credentials.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-md flex-col py-6">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
      >
        <div className="flex flex-col items-center gap-2 border-b border-slate-100 bg-slate-50/60 px-6 py-6">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-sm shadow-indigo-600/30">
            <ShieldCheck className="h-6 w-6" />
          </span>
          <h2 className="text-lg font-semibold text-slate-900">Sign in</h2>
          <p className="text-sm text-slate-500">Access your marksheet verification account</p>
        </div>

        <form onSubmit={onSubmit} className="space-y-4 px-6 py-6">
          <label className="block">
            <span className="text-xs font-medium text-slate-600">Email</span>
            <div className="relative mt-1">
              <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="h-10 w-full rounded-lg border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
              />
            </div>
          </label>

          <label className="block">
            <span className="text-xs font-medium text-slate-600">Password</span>
            <div className="relative mt-1">
              <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Your password"
                className="h-10 w-full rounded-lg border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
              />
            </div>
          </label>

          {error && (
            <p className="flex items-start gap-1.5 text-sm text-red-600">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              {error}
            </p>
          )}

          <button type="submit" disabled={busy} className={buttonVariants({ variant: "primary" }) + " w-full"}>
            <LogIn className="h-4 w-4" />
            {busy ? "Signing in…" : "Sign in"}
          </button>

          <p className="text-center text-sm text-slate-500">
            New student?{" "}
            <Link to="/register" className="font-medium text-indigo-600 hover:text-indigo-700">
              Create an account
            </Link>
          </p>
        </form>
      </motion.div>

      <p className="mt-4 text-center text-xs text-slate-400">
        Admin / reviewer accounts are created by staff and cannot be self-registered.
      </p>
    </div>
  );
}

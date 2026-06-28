import { useState } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "motion/react";
import { Send, CheckCircle2, Copy, Check, ArrowRight, AlertCircle, Info } from "lucide-react";
import FileUpload from "../components/FileUpload";
import StatusBadge from "../components/StatusBadge";
import { submitStudentMarksheet } from "../api";
import { buttonVariants } from "../lib/utils";

// A single labelled text input.
function Field({ label, value, onChange, type = "text", placeholder, required }) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-slate-600">
        {label}
        {required && <span className="text-red-500"> *</span>}
      </span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="mt-1 h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
      />
    </label>
  );
}

export default function StudentUpload() {
  const [form, setForm] = useState({
    student_name: "",
    student_email: "",
    application_id: "",
    board_name: "",
    exam_year: "",
  });
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | submitting | done | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const set = (key) => (val) => setForm((f) => ({ ...f, [key]: val }));

  async function submit() {
    if (!file || status === "submitting") return;
    setStatus("submitting");
    setError("");
    try {
      const data = await submitStudentMarksheet(file, form);
      setResult(data);
      setStatus("done");
    } catch (err) {
      setError(err.message || "Submission failed. Please try again.");
      setStatus("error");
    }
  }

  function copyId() {
    try {
      navigator.clipboard?.writeText(result.case_id);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  }

  function reset() {
    setForm({ student_name: "", student_email: "", application_id: "", board_name: "", exam_year: "" });
    setFile(null);
    setResult(null);
    setError("");
    setStatus("idle");
  }

  // Success screen
  if (status === "done" && result) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mx-auto max-w-xl space-y-5"
      >
        <div className="overflow-hidden rounded-xl border border-emerald-200 bg-white shadow-sm">
          <div className="flex items-center gap-2 border-b border-emerald-100 bg-emerald-50/60 px-5 py-4">
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
            <h2 className="text-sm font-semibold text-slate-900">Submission received</h2>
          </div>
          <div className="space-y-4 px-5 py-5">
            <p className="text-sm text-slate-600">{result.message}</p>

            <div className="rounded-lg bg-slate-50 px-4 py-3">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                Your submission ID
              </p>
              <div className="mt-1 flex items-center gap-2">
                <span className="font-mono text-sm font-semibold text-slate-800">{result.case_id}</span>
                <button
                  onClick={copyId}
                  className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                >
                  {copied ? <Check className="h-3 w-3 text-emerald-600" /> : <Copy className="h-3 w-3" />}
                  {copied ? "Copied" : "Copy"}
                </button>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-500">Status:</span>
              <StatusBadge status={result.status} size="sm" />
            </div>

            {result.next_steps?.length > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Next steps</p>
                <ul className="mt-1 space-y-1">
                  {result.next_steps.map((s, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-indigo-400" />
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="flex flex-wrap gap-3 pt-2">
              <Link to={`/track?case_id=${encodeURIComponent(result.case_id)}`} className={buttonVariants({ variant: "primary" })}>
                Track this submission <ArrowRight className="h-4 w-4" />
              </Link>
              <button onClick={reset} className={buttonVariants({ variant: "secondary" })}>
                Submit another
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    );
  }

  // Form screen
  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Submit your marksheet</h2>
        <p className="mt-1 text-sm text-slate-500">
          Upload your Class 10 / 12 marksheet for verification. You'll get a submission ID to
          track your status. The university team reviews every submission.
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Full name" value={form.student_name} onChange={set("student_name")} placeholder="Your name" />
          <Field label="Email" type="email" value={form.student_email} onChange={set("student_email")} placeholder="you@example.com" />
          <Field label="Application ID" value={form.application_id} onChange={set("application_id")} placeholder="e.g. APP-2026-001" />
          <Field label="Board (optional)" value={form.board_name} onChange={set("board_name")} placeholder="e.g. CBSE / ICSE / State Board" />
          <Field label="Exam year (optional)" value={form.exam_year} onChange={set("exam_year")} placeholder="e.g. 2020" />
        </div>

        <div className="mt-5">
          <span className="text-xs font-medium text-slate-600">Marksheet file (PDF / JPG / PNG) *</span>
          <div className="mt-1.5">
            <FileUpload
              selectedFile={file}
              onSelect={setFile}
              onClear={() => setFile(null)}
              disabled={status === "submitting"}
            />
          </div>
        </div>

        <div className="mt-5 flex items-center gap-3">
          <button onClick={submit} disabled={!file || status === "submitting"} className={buttonVariants({ variant: "primary" })}>
            <Send className="h-4 w-4" />
            {status === "submitting" ? "Submitting…" : "Submit for verification"}
          </button>
        </div>

        {status === "error" && (
          <p className="mt-3 flex items-start gap-1.5 text-sm text-red-600">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            {error}
          </p>
        )}
      </div>

      <div className="flex items-start gap-2 rounded-xl border border-indigo-100 bg-indigo-50/60 px-4 py-3">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-indigo-600" />
        <p className="text-xs text-slate-600">
          Please upload a clear scan or photo. Do not upload anyone else's documents. Your
          submission is reviewed by a person — automated checks only assist the reviewer.
        </p>
      </div>
    </div>
  );
}

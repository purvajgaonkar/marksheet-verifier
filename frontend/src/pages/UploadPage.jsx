import { useState } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "motion/react";
import {
  Sparkles,
  ArrowRight,
  FileCheck2,
  RotateCcw,
  AlertCircle,
  ScanText,
  Fingerprint,
  Gauge,
  Check,
} from "lucide-react";
import FileUpload from "../components/FileUpload";
import RiskBadge, { getRiskMeta } from "../components/RiskBadge";
import { uploadFile } from "../api";
import { buttonVariants, cn } from "../lib/utils";

// Three-step progress indicator across the top of the page.
const STEPS = ["Select file", "Analyze", "Review result"];

function StepIndicator({ current }) {
  return (
    <div className="flex items-center">
      {STEPS.map((label, i) => {
        const state = i < current ? "done" : i === current ? "active" : "todo";
        return (
          <div key={label} className="flex flex-1 items-center last:flex-none">
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold ring-1 ring-inset transition-colors",
                  state === "done" && "bg-indigo-600 text-white ring-indigo-600",
                  state === "active" && "bg-indigo-50 text-indigo-700 ring-indigo-300",
                  state === "todo" && "bg-white text-slate-400 ring-slate-200"
                )}
              >
                {state === "done" ? <Check className="h-4 w-4" /> : i + 1}
              </span>
              <span
                className={cn(
                  "hidden text-sm font-medium sm:block",
                  state === "todo" ? "text-slate-400" : "text-slate-700"
                )}
              >
                {label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <span
                className={cn(
                  "mx-3 h-px flex-1 transition-colors",
                  i < current ? "bg-indigo-300" : "bg-slate-200"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

// Animated "pipeline" shown while the backend analyzes the file.
const PIPELINE = [
  { Icon: ScanText, label: "Running OCR" },
  { Icon: Fingerprint, label: "Inspecting metadata" },
  { Icon: Gauge, label: "Scoring risk signals" },
];

function AnalyzingPanel() {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="space-y-3">
        {PIPELINE.map((p, i) => (
          <motion.div
            key={p.label}
            initial={{ opacity: 0.4 }}
            animate={{ opacity: [0.4, 1, 0.4] }}
            transition={{ duration: 1.4, repeat: Infinity, delay: i * 0.25 }}
            className="flex items-center gap-3"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
              <p.Icon className="h-5 w-5" />
            </span>
            <span className="text-sm font-medium text-slate-600">{p.label}…</span>
          </motion.div>
        ))}
      </div>
      <p className="mt-4 text-xs text-slate-400">
        This usually takes a couple of seconds.
      </p>
    </div>
  );
}

// One labelled value in the result summary grid.
function ResultField({ label, value, mono }) {
  return (
    <div className="rounded-lg bg-slate-50 px-4 py-3">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
      <p className={cn("mt-1 text-sm font-medium text-slate-800", mono && "font-mono")}>{value}</p>
    </div>
  );
}

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | uploading | done | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function handleUpload() {
    if (!file) return;
    setStatus("uploading");
    setError("");
    setResult(null);
    try {
      const data = await uploadFile(file);
      setResult(data);
      setStatus("done");
    } catch (err) {
      setError(err.message || "Upload failed.");
      setStatus("error");
    }
  }

  function reset() {
    setFile(null);
    setResult(null);
    setError("");
    setStatus("idle");
  }

  const uploading = status === "uploading";
  const currentStep = status === "done" ? 2 : uploading ? 1 : 0;
  const riskMeta = result ? getRiskMeta(result.risk_label) : null;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Upload a marksheet</h2>
        <p className="mt-1 text-sm text-slate-500">
          We extract text, inspect metadata, and produce a risk signal report. This is an
          MVP signal report, not final proof of tampering.
        </p>
      </div>

      {/* Step indicator */}
      <div className="rounded-xl border border-slate-200 bg-white px-5 py-4 shadow-sm">
        <StepIndicator current={currentStep} />
      </div>

      {/* Upload card (hidden once we have a result, to keep focus on the report) */}
      {status !== "done" && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <FileUpload
            selectedFile={file}
            onSelect={setFile}
            onClear={reset}
            disabled={uploading}
          />

          <div className="mt-5 flex items-center gap-3">
            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className={buttonVariants({ variant: "primary" })}
            >
              {uploading ? (
                <>
                  <Sparkles className="h-4 w-4 animate-pulse" />
                  Analyzing…
                </>
              ) : (
                <>
                  <FileCheck2 className="h-4 w-4" />
                  Analyze marksheet
                </>
              )}
            </button>
            {file && !uploading && (
              <button onClick={reset} className={buttonVariants({ variant: "ghost" })}>
                <RotateCcw className="h-4 w-4" />
                Clear
              </button>
            )}
          </div>
        </div>
      )}

      {/* Analyzing animation */}
      <AnimatePresence>
        {uploading && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            <AnalyzingPanel />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error */}
      <AnimatePresence>
        {status === "error" && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50/60 px-5 py-4"
          >
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
            <div>
              <p className="text-sm font-medium text-slate-800">Upload failed</p>
              <p className="mt-0.5 text-sm text-slate-600">{error}</p>
              <p className="mt-1 text-xs text-slate-400">
                Is the backend running at http://127.0.0.1:8000 ?
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Animated result card with a risk-colored header */}
      <AnimatePresence>
        {status === "done" && result && riskMeta && (
          <motion.div
            initial={{ opacity: 0, y: 16, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35, ease: "easeOut" }}
            className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"
          >
            <div className={cn("flex items-center justify-between px-5 py-4", riskMeta.classes)}>
              <div className="flex items-center gap-2">
                <riskMeta.Icon className="h-5 w-5" />
                <h3 className="text-sm font-semibold">Analysis complete</h3>
              </div>
              <RiskBadge label={result.risk_label} />
            </div>

            <div className="grid grid-cols-2 gap-3 px-5 py-5">
              <ResultField label="Case ID" value={result.case_id} mono />
              <ResultField label="Filename" value={result.filename} />
              <ResultField label="Risk score" value={result.risk_score ?? "—"} />
              <ResultField
                label="OCR confidence"
                value={result.ocr_confidence != null ? `${result.ocr_confidence} / 100` : "—"}
              />
            </div>

            <div className="flex flex-wrap items-center gap-3 border-t border-slate-100 px-5 py-4">
              <Link to={`/cases/${result.case_id}`} className={buttonVariants({ variant: "primary" })}>
                View full report <ArrowRight className="h-4 w-4" />
              </Link>
              <button onClick={reset} className={buttonVariants({ variant: "secondary" })}>
                <RotateCcw className="h-4 w-4" />
                Upload another
              </button>
              <Link to="/admin" className={buttonVariants({ variant: "ghost" })}>
                Go to dashboard
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

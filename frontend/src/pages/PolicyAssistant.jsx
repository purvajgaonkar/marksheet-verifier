import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "motion/react";
import {
  Send,
  Sparkles,
  BookOpen,
  Info,
  Library,
  FileText,
  MessageSquareText,
  User,
  ServerCog,
  AlertTriangle,
} from "lucide-react";
import RiskBadge from "../components/RiskBadge";
import ModeBadge from "../components/ModeBadge";
import { askPolicyAssistant, getRagSources, getCases, getLlmStatus } from "../api";
import { buttonVariants, cn } from "../lib/utils";

const STARTER_QUESTIONS = [
  "Why is metadata warning not proof?",
  "What should I do for a high-risk case?",
  "How should OCR confidence be interpreted?",
  "Are pixel forensics reliable?",
  "What does needs_review mean?",
  "Should the student be rejected automatically?",
];

// Compact chips summarising the case the answer was grounded in.
function CaseSummaryChips({ summary }) {
  if (!summary || !summary.found) return null;
  const chip = "inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-1 text-xs font-medium ring-1 ring-inset ring-slate-200 text-slate-600";
  return (
    <div className="mt-3 flex flex-wrap items-center gap-2">
      <span className="text-xs font-medium text-slate-400">Case {summary.case_id}:</span>
      {summary.risk_label && <RiskBadge label={summary.risk_label} size="sm" />}
      {summary.risk_score != null && <span className={chip}>score {summary.risk_score}</span>}
      {summary.ocr_confidence != null && <span className={chip}>OCR {summary.ocr_confidence}/100</span>}
      <span className={chip}>{summary.metadata_flag_count} metadata flag{summary.metadata_flag_count === 1 ? "" : "s"}</span>
      {summary.forensics_anomaly_score != null && (
        <span className={chip}>anomaly {summary.forensics_anomaly_score}</span>
      )}
    </div>
  );
}

function AnswerCard({ turn }) {
  const r = turn.response;
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center gap-2">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
          <Sparkles className="h-4 w-4" />
        </span>
        <span className="text-sm font-semibold text-slate-900">Policy Assistant</span>
        <ModeBadge mode={r.mode} model={r.model} />
      </div>

      {r.llm_error && (
        <p className="mt-2 flex items-start gap-1.5 text-xs text-amber-700">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          Claude was unavailable, so this used the local fallback. ({r.llm_error})
        </p>
      )}

      <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">{r.answer}</p>

      <CaseSummaryChips summary={r.case_summary} />

      {r.sources?.length > 0 && (
        <div className="mt-4">
          <p className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
            <BookOpen className="h-3.5 w-3.5" /> Sources used
          </p>
          <div className="grid gap-2 sm:grid-cols-2">
            {r.sources.map((s, i) => (
              <div key={i} className="rounded-lg bg-slate-50 px-3 py-2 ring-1 ring-inset ring-slate-100">
                <p className="flex items-center gap-1.5 text-xs font-medium text-slate-700">
                  <FileText className="h-3.5 w-3.5 text-slate-400" />
                  {s.document}
                  <span className="font-mono text-[10px] text-slate-400">{s.chunk_id}</span>
                </p>
                <p className="mt-1 text-xs text-slate-500">{s.preview}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {r.limitations?.length > 0 && (
        <div className="mt-4 flex items-start gap-2 rounded-lg bg-indigo-50/60 px-3 py-2.5">
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-indigo-600" />
          <ul className="space-y-0.5 text-xs text-slate-600">
            {r.limitations.map((l, i) => (
              <li key={i}>{l}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function PolicyAssistant() {
  const [searchParams] = useSearchParams();
  const [question, setQuestion] = useState("");
  const [caseId, setCaseId] = useState(searchParams.get("case_id") || "");
  const [cases, setCases] = useState([]);
  const [turns, setTurns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sourcesInfo, setSourcesInfo] = useState(null);
  const [llmStatus, setLlmStatus] = useState(null);
  const [llmChecking, setLlmChecking] = useState(false);
  const bottomRef = useRef(null);

  // Load case list (for the dropdown), index info, and LLM status on mount.
  useEffect(() => {
    getCases().then(setCases).catch(() => setCases([]));
    getRagSources().then(setSourcesInfo).catch(() => setSourcesInfo(null));
    getLlmStatus().then(setLlmStatus).catch(() => setLlmStatus(null));
  }, []);

  async function checkLlm() {
    setLlmChecking(true);
    try {
      setLlmStatus(await getLlmStatus());
    } catch {
      setLlmStatus(null);
    } finally {
      setLlmChecking(false);
    }
  }

  // Keep the latest answer in view.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, loading]);

  async function ask(q) {
    const text = (q ?? question).trim();
    if (!text || loading) return;
    setLoading(true);
    setError("");
    try {
      const response = await askPolicyAssistant(text, caseId || undefined);
      setTurns((prev) => [...prev, { question: text, response }]);
      setQuestion("");
    } catch (err) {
      setError(err.message || "The assistant could not answer. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      {/* Header */}
      <div>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Policy Assistant</h2>
            <p className="mt-1 max-w-xl text-sm text-slate-500">
              Ask about verification rules, ethics, limitations, and next steps. Answers are
              grounded in this project's local policy documents. Claude can optionally phrase
              them when enabled — otherwise a local fallback is used.
            </p>
          </div>
          <button
            onClick={checkLlm}
            disabled={llmChecking}
            className={buttonVariants({ variant: "secondary", size: "sm" })}
          >
            <ServerCog className={cn("h-4 w-4", llmChecking && "animate-spin")} />
            Check LLM Status
          </button>
        </div>

        <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-400">
          {sourcesInfo && (
            <span className="flex items-center gap-1.5">
              <Library className="h-3.5 w-3.5" />
              {sourcesInfo.chunk_count} chunks · {sourcesInfo.documents?.length} docs ({sourcesInfo.mode})
            </span>
          )}
          {llmStatus && (
            <span
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 font-medium ring-1 ring-inset",
                llmStatus.mode === "claude_rag"
                  ? "bg-indigo-50 text-indigo-700 ring-indigo-200"
                  : "bg-slate-100 text-slate-600 ring-slate-200"
              )}
              title={`LLM enabled: ${llmStatus.llm_enabled} · API key configured: ${llmStatus.api_key_configured}`}
            >
              <Sparkles className="h-3.5 w-3.5" />
              {llmStatus.mode === "claude_rag"
                ? `Claude RAG · ${llmStatus.model}`
                : "Local fallback"}
            </span>
          )}
        </div>
      </div>

      {/* Case selector */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <label className="text-xs font-medium uppercase tracking-wide text-slate-400">
          Ask about a specific case (optional)
        </label>
        <select
          value={caseId}
          onChange={(e) => setCaseId(e.target.value)}
          className="mt-1.5 h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
        >
          <option value="">No specific case (general policy questions)</option>
          {cases.map((c) => (
            <option key={c.case_id} value={c.case_id}>
              {c.filename} — {c.case_id} ({c.risk_label})
            </option>
          ))}
        </select>
      </div>

      {/* Starter chips */}
      <div className="flex flex-wrap gap-2">
        {STARTER_QUESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => ask(q)}
            disabled={loading}
            className="rounded-full bg-white px-3 py-1.5 text-xs font-medium text-slate-600 ring-1 ring-inset ring-slate-200 transition-colors hover:bg-indigo-50 hover:text-indigo-700 hover:ring-indigo-200 disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Conversation */}
      <div className="space-y-4">
        {turns.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-white py-12 text-center">
            <MessageSquareText className="h-8 w-8 text-slate-300" />
            <p className="mt-3 text-sm text-slate-500">
              Ask a question above, or tap a starter question to begin.
            </p>
          </div>
        )}

        {turns.map((turn, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
            className="space-y-3"
          >
            {/* Question bubble */}
            <div className="flex items-start justify-end gap-2">
              <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-indigo-600 px-4 py-2.5 text-sm text-white shadow-sm">
                {turn.question}
              </div>
              <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-200 text-slate-500">
                <User className="h-4 w-4" />
              </span>
            </div>
            {/* Answer */}
            <AnswerCard turn={turn} />
          </motion.div>
        ))}

        <AnimatePresence>
          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-4 text-sm text-slate-500 shadow-sm"
            >
              <Sparkles className="h-4 w-4 animate-pulse text-indigo-600" />
              Retrieving policy guidance…
            </motion.div>
          )}
        </AnimatePresence>

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50/60 px-5 py-4 text-sm text-red-700">
            {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="sticky bottom-4 rounded-xl border border-slate-200 bg-white p-3 shadow-md">
        <div className="flex items-end gap-2">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                ask();
              }
            }}
            rows={1}
            placeholder="Ask the policy assistant… (Enter to send, Shift+Enter for a new line)"
            className="max-h-32 min-h-[40px] flex-1 resize-none rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
          <button
            onClick={() => ask()}
            disabled={loading || !question.trim()}
            className={buttonVariants({ variant: "primary" })}
          >
            <Send className="h-4 w-4" />
            Ask
          </button>
        </div>
      </div>
    </div>
  );
}

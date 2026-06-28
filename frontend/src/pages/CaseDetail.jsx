import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Info,
  ListChecks,
  FileText,
  Fingerprint,
  ScanText,
  Gauge,
  ClipboardCheck,
  CheckCircle2,
  FileQuestion,
  XCircle,
  HelpCircle,
  Copy,
  Check,
  MessageSquareText,
  Sparkles,
  BookOpen,
  Loader2,
  Send,
  History,
  ScrollText,
  UserCircle2,
} from "lucide-react";
import RiskBadge, { getRiskMeta } from "../components/RiskBadge";
import ReportSection from "../components/ReportSection";
import ModeBadge from "../components/ModeBadge";
import ForensicsPanel from "../components/ForensicsPanel";
import AgentTracePanel from "../components/AgentTracePanel";
import ErrorState from "../components/ErrorState";
import { Skeleton } from "../components/Skeleton";
import StatusBadge from "../components/StatusBadge";
import { getReport, generateCaseExplanation, getAdminCase, postAdminDecision } from "../api";
import { buttonVariants, cn, formatDateTime } from "../lib/utils";

// ---------------------------------------------------------------------------
// Phase 8: reviewer decisions are now persisted to the database via
// POST /admin/cases/{case_id}/decision. The system never auto-decides — this
// panel records a HUMAN reviewer's action and updates the student-facing status.
// ---------------------------------------------------------------------------
const DECISION_OPTIONS = [
  { value: "approved", label: "Approved" },
  { value: "needs_more_documents", label: "Needs more documents" },
  { value: "request_official_verification", label: "Request official verification" },
  { value: "rejected_after_manual_review", label: "Rejected (after manual review)" },
  { value: "unable_to_verify", label: "Unable to verify" },
];

const STUDENT_STATUS_OPTIONS = [
  { value: "verified", label: "Verified" },
  { value: "reupload_required", label: "Re-upload required" },
  { value: "official_verification_required", label: "Official verification required" },
  { value: "under_review", label: "Under review" },
  { value: "closed", label: "Closed" },
];

// Sensible student-status default for each decision.
const DECISION_TO_STATUS = {
  approved: "verified",
  needs_more_documents: "reupload_required",
  request_official_verification: "official_verification_required",
  rejected_after_manual_review: "closed",
  unable_to_verify: "under_review",
};

const DECISION_LABELS = Object.fromEntries(DECISION_OPTIONS.map((d) => [d.value, d.label]));

// A one-line, non-accusatory explanation of each risk label for the banner.
const RISK_MEANING = {
  verified: "No tampering signals were detected by the automated checks.",
  low: "Only minor signals were found — most likely fine.",
  medium: "Some signals were found; a quick human glance is suggested.",
  needs_review: "Enough signals that manual review is recommended.",
  high: "Multiple strong signals — please prioritise manual review.",
  unable_to_verify: "The document could not be analysed automatically.",
  unknown: "No risk information is available for this case.",
};

// A simple "label : value" row used in the detected-fields block.
function Field({ label, value }) {
  const has =
    value !== null && value !== undefined && value !== "" &&
    !(Array.isArray(value) && value.length === 0);
  return (
    <div className="flex items-start justify-between gap-4 py-2 border-b border-slate-100 last:border-0">
      <span className="text-sm text-slate-500">{label}</span>
      <span className={cn("text-sm text-right", has ? "font-medium text-slate-800" : "text-slate-400")}>
        {has ? (Array.isArray(value) ? value.join(", ") : String(value)) : "Not detected"}
      </span>
    </div>
  );
}

// Curated metadata keys worth showing (only those present appear).
const META_KEYS = [
  "FileType", "MIMEType", "FileSize", "Software", "Creator", "Producer",
  "CreatorTool", "CreateDate", "ModifyDate", "ImageWidth", "ImageHeight",
  "XMPToolkit", "PageCount",
];

function CaseDetailSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-4 w-40" />
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <Skeleton className="h-3 w-32" />
        <Skeleton className="mt-3 h-6 w-64" />
        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16" />
          ))}
        </div>
      </div>
      <Skeleton className="h-24 rounded-xl" />
      <div className="grid gap-6 lg:grid-cols-2">
        <Skeleton className="h-48 rounded-xl" />
        <Skeleton className="h-48 rounded-xl" />
      </div>
    </div>
  );
}

export default function CaseDetail() {
  const { caseId } = useParams();
  const [report, setReport] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  // Phase 8: database-backed case detail (status, decisions, audit trail).
  const [admin, setAdmin] = useState(null);
  const [form, setForm] = useState({
    decision: "approved",
    student_status: "verified",
    reviewer_comment: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [decisionError, setDecisionError] = useState("");

  // Phase 7: optional LLM explanation of this case.
  const [explanation, setExplanation] = useState(null);
  const [explaining, setExplaining] = useState(false);
  const [explainError, setExplainError] = useState("");

  async function handleExplain() {
    setExplaining(true);
    setExplainError("");
    try {
      setExplanation(await generateCaseExplanation(caseId));
    } catch (err) {
      setExplainError(err.message || "Could not generate an explanation.");
    } finally {
      setExplaining(false);
    }
  }

  const loadAdmin = useCallback(async () => {
    try {
      setAdmin(await getAdminCase(caseId));
    } catch {
      setAdmin(null); // case may predate the DB; the report panels still work
    }
  }, [caseId]);

  const load = useCallback(async () => {
    setStatus("loading");
    setError("");
    try {
      const data = await getReport(caseId);
      setReport(data);
      setStatus("ready");
    } catch (err) {
      setError(err.message || "Could not load report.");
      setStatus("error");
    }
    loadAdmin();
  }, [caseId, loadAdmin]);

  useEffect(() => {
    load();
  }, [load]);

  // When the reviewer picks a decision, default the student status sensibly.
  function setDecisionValue(value) {
    setForm((f) => ({
      ...f,
      decision: value,
      student_status: DECISION_TO_STATUS[value] || f.student_status,
    }));
  }

  async function submitDecision() {
    setSubmitting(true);
    setDecisionError("");
    try {
      await postAdminDecision(caseId, {
        decision: form.decision,
        reviewer_comment: form.reviewer_comment.trim() || null,
        student_status: form.student_status,
      });
      setForm((f) => ({ ...f, reviewer_comment: "" }));
      await loadAdmin();
    } catch (err) {
      setDecisionError(err.message || "Could not record the decision.");
    } finally {
      setSubmitting(false);
    }
  }

  function copyCaseId() {
    const id = report?.case_id || caseId;
    try {
      navigator.clipboard?.writeText(id);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  }

  if (status === "loading") return <CaseDetailSkeleton />;
  if (status === "error")
    return (
      <div className="space-y-4">
        <BackLink />
        <ErrorState
          title="Could not load this case"
          message={error}
          command="python -m uvicorn app.main:app --reload --app-dir backend"
          onRetry={load}
        />
      </div>
    );

  const risk = report.risk || {};
  const ocr = report.ocr || {};
  const fields = report.detected_fields || {};
  const metadata = report.metadata || {};
  const flags = metadata.flags || [];
  const flagDetails = metadata.flag_details || {};
  const raw = metadata.raw || {};
  const riskMeta = getRiskMeta(risk.label);
  const disclaimer =
    report.disclaimer || "This is an MVP signal report, not final proof of tampering.";
  const presentMeta = META_KEYS.filter(
    (k) => raw[k] !== undefined && raw[k] !== null && raw[k] !== ""
  );

  return (
    <div className="space-y-6">
      <BackLink />

      {/* Risk-colored summary banner */}
      <div className={cn("rounded-xl px-5 py-4 ring-1 ring-inset", riskMeta.classes)}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <riskMeta.Icon className="h-6 w-6 shrink-0" />
            <div>
              <p className="text-sm font-semibold">{riskMeta.label}</p>
              <p className="text-sm opacity-90">{RISK_MEANING[risk.label] || RISK_MEANING.unknown}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs uppercase tracking-wide opacity-70">Risk score</p>
            <p className="text-2xl font-bold tabular-nums">{risk.score ?? "—"}</p>
          </div>
        </div>
      </div>

      {/* Header card */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="font-mono text-xs text-slate-400">{report.case_id || caseId}</p>
              <button
                onClick={copyCaseId}
                className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                title="Copy case ID"
              >
                {copied ? <Check className="h-3 w-3 text-emerald-600" /> : <Copy className="h-3 w-3" />}
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
            <h2 className="mt-1 truncate text-xl font-semibold text-slate-900">
              {report.file?.name || "Marksheet report"}
            </h2>
            <p className="mt-0.5 text-sm text-slate-500">Analyzed {report.analyzed_at || "—"}</p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <RiskBadge label={risk.label} />
            <Link
              to={`/assistant?case_id=${encodeURIComponent(report.case_id || caseId)}`}
              className={buttonVariants({ variant: "secondary", size: "sm" })}
            >
              <MessageSquareText className="h-3.5 w-3.5" />
              Ask Policy Assistant about this case
            </Link>
          </div>
        </div>

        {/* Quick metrics */}
        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Metric Icon={Gauge} label="Risk score" value={risk.score ?? "—"} />
          <Metric Icon={ScanText} label="OCR confidence" value={ocr.average_confidence != null ? `${ocr.average_confidence}` : "—"} />
          <Metric Icon={Fingerprint} label="Board" value={fields.board || "unknown"} />
          <Metric Icon={FileText} label="File type" value={report.file?.type || "—"} />
        </div>
      </div>

      {/* Important note */}
      <div className="flex items-start gap-3 rounded-xl border border-indigo-100 bg-indigo-50/60 px-5 py-4">
        <Info className="mt-0.5 h-5 w-5 shrink-0 text-indigo-600" />
        <p className="text-sm text-slate-700">
          <span className="font-medium">Important: </span>
          {disclaimer} Risk labels are automated signals only — a human reviewer makes the
          final decision.
        </p>
      </div>

      {/* Agentic workflow trace (Phase 5) */}
      <AgentTracePanel workflow={report.agentic_workflow} />

      {/* LLM explanation (Phase 7) */}
      <ReportSection title="AI explanation for reviewers" Icon={Sparkles}>
        <p className="text-sm text-slate-500">
          Generate a source-grounded, plain-English explanation of this case. Uses Claude
          when enabled, otherwise a local fallback. This is a review aid only — it does not
          change the case, the risk score, or any decision.
        </p>
        <button
          onClick={handleExplain}
          disabled={explaining}
          className={buttonVariants({ variant: "primary" }) + " mt-4"}
        >
          {explaining ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Generating…
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              {explanation ? "Regenerate explanation" : "Generate LLM Explanation"}
            </>
          )}
        </button>

        {explainError && (
          <p className="mt-3 text-sm text-red-600">{explainError}</p>
        )}

        {explanation && (
          <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <ModeBadge mode={explanation.mode} model={explanation.model} />
              {explanation.llm_error && (
                <span className="text-xs text-amber-700">
                  Claude unavailable — used local fallback.
                </span>
              )}
            </div>

            <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
              {explanation.explanation}
            </p>

            {explanation.sources?.length > 0 && (
              <div className="mt-4">
                <p className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
                  <BookOpen className="h-3.5 w-3.5" /> Sources used
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {explanation.sources.map((s, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1 rounded-full bg-white px-2 py-0.5 text-[11px] font-medium text-slate-600 ring-1 ring-inset ring-slate-200"
                      title={s.preview}
                    >
                      {s.document}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {explanation.limitations?.length > 0 && (
              <ul className="mt-3 space-y-0.5 text-xs text-slate-500">
                {explanation.limitations.map((l, i) => (
                  <li key={i}>• {l}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </ReportSection>

      {/* Reviewer decision (Phase 8, database-backed) */}
      <ReportSection
        title="Reviewer decision"
        Icon={ClipboardCheck}
        action={
          admin?.case?.status ? <StatusBadge status={admin.case.status} size="sm" /> : null
        }
      >
        <p className="text-sm text-slate-500">
          Record a manual review outcome. This is a human decision — the system never
          auto-rejects a student. It updates the student-facing status and the audit trail.
        </p>

        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <label className="block">
            <span className="text-xs font-medium text-slate-600">Decision</span>
            <select
              value={form.decision}
              onChange={(e) => setDecisionValue(e.target.value)}
              className="mt-1 h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            >
              {DECISION_OPTIONS.map((d) => (
                <option key={d.value} value={d.value}>{d.label}</option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-xs font-medium text-slate-600">Student-facing status</span>
            <select
              value={form.student_status}
              onChange={(e) => setForm((f) => ({ ...f, student_status: e.target.value }))}
              className="mt-1 h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            >
              {STUDENT_STATUS_OPTIONS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </label>
        </div>

        <label className="mt-4 block">
          <span className="text-xs font-medium text-slate-600">Reviewer comment</span>
          <textarea
            value={form.reviewer_comment}
            onChange={(e) => setForm((f) => ({ ...f, reviewer_comment: e.target.value }))}
            rows={3}
            placeholder="e.g. OCR confidence is moderate. Requesting a clearer copy before final review."
            className="mt-1 w-full resize-none rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
        </label>

        <div className="mt-4 flex items-center gap-3">
          <button
            onClick={submitDecision}
            disabled={submitting}
            className={buttonVariants({ variant: "primary" })}
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            Submit decision
          </button>
          {!admin && (
            <span className="text-xs text-amber-700">
              This case isn't in the database yet — decisions can't be recorded.
            </span>
          )}
        </div>
        {decisionError && <p className="mt-2 text-sm text-red-600">{decisionError}</p>}
      </ReportSection>

      {/* Decision history + audit trail (Phase 8) */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ReportSection title="Review decision history" Icon={History}>
          {admin?.decisions?.length > 0 ? (
            <ul className="space-y-3">
              {[...admin.decisions].reverse().map((d) => (
                <li key={d.id} className="rounded-lg bg-slate-50 px-3 py-2.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium text-slate-800">
                      {DECISION_LABELS[d.decision] || d.decision}
                    </span>
                    <span className="text-xs text-slate-400">{formatDateTime(d.created_at)}</span>
                  </div>
                  {d.reviewer_comment && (
                    <p className="mt-1 text-xs text-slate-600">{d.reviewer_comment}</p>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">No reviewer decisions recorded yet.</p>
          )}
        </ReportSection>

        <ReportSection title="Audit trail" Icon={ScrollText}>
          {admin?.audit_logs?.length > 0 ? (
            <ul className="space-y-2">
              {[...admin.audit_logs].reverse().map((a) => (
                <li key={a.id} className="flex items-start gap-2 text-xs">
                  <UserCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-300" />
                  <div>
                    <span className="font-medium text-slate-700">{a.action.replaceAll("_", " ")}</span>
                    <span className="text-slate-400"> · {formatDateTime(a.created_at)}</span>
                    {a.details && <p className="text-slate-500">{a.details}</p>}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">No audit entries yet.</p>
          )}
        </ReportSection>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Detected fields */}
        <ReportSection title="Detected fields" Icon={ListChecks}>
          <Field label="Examination board" value={fields.board} />
          <Field label="Roll / seat number" value={fields.roll_number} />
          <Field label="Total marks" value={fields.total_marks} />
          <Field label="Percentage" value={fields.percentage != null ? `${fields.percentage}%` : null} />
          <Field label="Result keywords" value={fields.result_keywords} />
        </ReportSection>

        {/* Metadata warnings */}
        <ReportSection title="Metadata warnings" Icon={Fingerprint}>
          {flags.length === 0 ? (
            <div className="flex items-center gap-2 rounded-lg bg-emerald-50 px-3 py-2.5 text-sm text-emerald-700 ring-1 ring-inset ring-emerald-100">
              <CheckCircle2 className="h-4 w-4" />
              No metadata warning flags were raised.
            </div>
          ) : (
            <ul className="space-y-2.5">
              {flags.map((flag) => (
                <li key={flag} className="rounded-lg bg-amber-50 px-3 py-2 ring-1 ring-inset ring-amber-100">
                  <p className="text-sm font-medium capitalize text-amber-800">
                    {flag.replaceAll("_", " ")}
                  </p>
                  {flagDetails[flag] && (
                    <p className="mt-0.5 text-xs text-amber-700/80">{flagDetails[flag]}</p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </ReportSection>
      </div>

      {/* Risk factors */}
      {Array.isArray(risk.contributing_factors) && risk.contributing_factors.length > 0 && (
        <ReportSection title="What contributed to this risk score" Icon={Gauge}>
          <ul className="space-y-1.5">
            {risk.contributing_factors.map((factor, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-indigo-400" />
                {factor}
              </li>
            ))}
          </ul>
        </ReportSection>
      )}

      {/* Image / pixel forensics (Phase 4) */}
      <ForensicsPanel forensics={report.image_forensics} caseId={report.case_id || caseId} />

      {/* OCR text preview */}
      <ReportSection title="OCR text preview" Icon={ScanText}>
        <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-4 text-xs leading-relaxed text-slate-700">
          {ocr.full_text || ocr.text_preview || "No text was extracted."}
        </pre>
      </ReportSection>

      {/* Key metadata table */}
      <ReportSection title="Key metadata" Icon={FileText}>
        {presentMeta.length === 0 ? (
          <p className="text-sm text-slate-500">
            {metadata.metadata_available === false
              ? "Metadata could not be read for this file."
              : "No notable metadata fields were found."}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <tbody className="divide-y divide-slate-100">
                {presentMeta.map((key) => (
                  <tr key={key}>
                    <td className="py-2 pr-4 font-medium text-slate-500 whitespace-nowrap">{key}</td>
                    <td className="py-2 text-slate-800 break-all">{String(raw[key])}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </ReportSection>
    </div>
  );
}

function BackLink() {
  return (
    <Link
      to="/admin"
      className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-800"
    >
      <ArrowLeft className="h-4 w-4" />
      Back to dashboard
    </Link>
  );
}

function Metric({ Icon, label, value }) {
  return (
    <div className="rounded-lg bg-slate-50 px-4 py-3">
      <div className="flex items-center gap-1.5 text-slate-400">
        <Icon className="h-3.5 w-3.5" />
        <span className="text-xs font-medium uppercase tracking-wide">{label}</span>
      </div>
      <p className="mt-1 truncate text-sm font-semibold text-slate-800">{value}</p>
    </div>
  );
}

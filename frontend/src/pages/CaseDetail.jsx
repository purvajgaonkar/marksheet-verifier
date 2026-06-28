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
} from "lucide-react";
import RiskBadge, { getRiskMeta } from "../components/RiskBadge";
import ReportSection from "../components/ReportSection";
import ForensicsPanel from "../components/ForensicsPanel";
import AgentTracePanel from "../components/AgentTracePanel";
import ErrorState from "../components/ErrorState";
import { Skeleton } from "../components/Skeleton";
import { getReport } from "../api";
import { buttonVariants, cn } from "../lib/utils";

// ---------------------------------------------------------------------------
// Reviewer decisions. NOTE: the Phase 2 backend does not persist reviewer
// decisions yet, so we store the choice locally (localStorage) as a frontend-
// only placeholder.
// TODO(Phase 4+): replace localStorage with a real call, e.g.
//   PATCH /cases/{caseId} { status: <decision> }
// ---------------------------------------------------------------------------
const DECISIONS = [
  { key: "approved", label: "Approve", Icon: CheckCircle2, variant: "success" },
  { key: "needs_more_documents", label: "Request more documents", Icon: FileQuestion, variant: "secondary" },
  { key: "rejected_after_manual_review", label: "Reject (after manual review)", Icon: XCircle, variant: "danger" },
  { key: "unable_to_verify", label: "Mark unable to verify", Icon: HelpCircle, variant: "outline" },
];

const DECISION_BTN = {
  success: "bg-emerald-600 text-white hover:bg-emerald-700",
  secondary: "bg-white text-slate-700 border border-slate-200 hover:bg-slate-50",
  danger: "bg-red-600 text-white hover:bg-red-700",
  outline: "bg-white text-indigo-700 border border-indigo-200 hover:bg-indigo-50",
};

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
  const [decision, setDecision] = useState("");
  const [copied, setCopied] = useState(false);

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
  }, [caseId]);

  useEffect(() => {
    load();
    try {
      const saved = localStorage.getItem(`review_${caseId}`);
      if (saved) setDecision(saved);
    } catch {
      /* localStorage unavailable */
    }
  }, [load, caseId]);

  function recordDecision(key) {
    setDecision(key);
    try {
      localStorage.setItem(`review_${caseId}`, key);
    } catch {
      /* ignore */
    }
    // TODO(Phase 4+): persist to the backend instead of localStorage.
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

      {/* Reviewer actions */}
      <ReportSection title="Reviewer decision" Icon={ClipboardCheck}>
        <p className="text-sm text-slate-500">
          Record a manual review outcome. This is a recommendation workflow — the system
          never auto-rejects a student.
        </p>
        <div className="mt-4 flex flex-wrap gap-2.5">
          {DECISIONS.map(({ key, label, Icon, variant }) => (
            <button
              key={key}
              onClick={() => recordDecision(key)}
              className={cn(
                "inline-flex items-center gap-2 rounded-lg px-4 h-10 text-sm font-medium shadow-sm transition-colors",
                DECISION_BTN[variant],
                decision === key && "ring-2 ring-indigo-500 ring-offset-2"
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>
        {decision && (
          <p className="mt-3 text-xs text-slate-500">
            Current decision:{" "}
            <span className="font-medium text-slate-700">
              {DECISIONS.find((d) => d.key === decision)?.label}
            </span>{" "}
            — saved locally in this browser only (not yet sent to the backend).
          </p>
        )}
      </ReportSection>

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

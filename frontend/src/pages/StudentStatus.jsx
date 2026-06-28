// ---------------------------------------------------------------------------
// StudentStatus.jsx -> "Track My Submissions" (Phase 9)
// ---------------------------------------------------------------------------
// Shows the logged-in student's own submissions (GET /student/my-submissions),
// plus an optional lookup by submission ID. Safe wording only — never any
// internal risk score, forensics, metadata, agent trace, or AI explanation.
// ---------------------------------------------------------------------------
import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { motion } from "motion/react";
import {
  Search,
  AlertCircle,
  Clock,
  AlertTriangle,
  RefreshCcw,
  FileText,
  Inbox,
  Loader2,
} from "lucide-react";
import StatusBadge from "../components/StatusBadge";
import { getMySubmissions, getStudentSubmission } from "../api";
import { buttonVariants, formatDateTime } from "../lib/utils";

// One submission card (used for both the list and the single lookup result).
function SubmissionCard({ item, highlight }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={
        "rounded-xl border bg-white p-5 shadow-sm " +
        (highlight ? "border-indigo-300 ring-2 ring-indigo-100" : "border-slate-200")
      }
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-slate-500">
          <FileText className="h-4 w-4 shrink-0" />
          <span className="truncate text-sm font-medium text-slate-700">
            {item.original_filename || "Marksheet"}
          </span>
        </div>
        <StatusBadge status={item.status} />
      </div>

      <p className="mt-2 font-mono text-xs text-slate-400">{item.case_id}</p>

      {item.action_required && item.action_message && (
        <div className="mt-3 flex items-start gap-2 rounded-lg bg-orange-50 px-3 py-2.5 ring-1 ring-inset ring-orange-100">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-orange-600" />
          <p className="text-sm text-orange-800">{item.action_message}</p>
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-4 text-xs text-slate-400">
        <span className="flex items-center gap-1.5">
          <Clock className="h-3.5 w-3.5" />
          Submitted {formatDateTime(item.created_at || item.submitted_at)}
        </span>
        {item.updated_at && (
          <span className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            Updated {formatDateTime(item.updated_at)}
          </span>
        )}
      </div>
    </motion.div>
  );
}

export default function StudentStatus() {
  const [searchParams] = useSearchParams();
  const highlightId = searchParams.get("case_id") || "";

  const [items, setItems] = useState([]);
  const [listStatus, setListStatus] = useState("loading"); // loading | done | error
  const [listError, setListError] = useState("");

  // Optional lookup-by-id (one of your own submissions).
  const [caseId, setCaseId] = useState("");
  const [lookupStatus, setLookupStatus] = useState("idle"); // idle | loading | done | error
  const [lookup, setLookup] = useState(null);
  const [lookupError, setLookupError] = useState("");

  const loadList = useCallback(async () => {
    setListStatus("loading");
    setListError("");
    try {
      setItems(await getMySubmissions());
      setListStatus("done");
    } catch (err) {
      setListError(err.message || "Could not load your submissions.");
      setListStatus("error");
    }
  }, []);

  useEffect(() => {
    loadList();
  }, [loadList]);

  async function lookupById() {
    const value = caseId.trim();
    if (!value) return;
    setLookupStatus("loading");
    setLookupError("");
    setLookup(null);
    try {
      setLookup(await getStudentSubmission(value));
      setLookupStatus("done");
    } catch (err) {
      setLookupError(err.message || "Submission not found.");
      setLookupStatus("error");
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-end justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">My submissions</h2>
          <p className="mt-1 text-sm text-slate-500">
            Track the status of the marksheets you've submitted for verification.
          </p>
        </div>
        <button
          onClick={loadList}
          disabled={listStatus === "loading"}
          className={buttonVariants({ variant: "secondary", size: "sm" })}
        >
          <RefreshCcw className={"h-3.5 w-3.5 " + (listStatus === "loading" ? "animate-spin" : "")} />
          Refresh
        </button>
      </div>

      {/* Submission list */}
      {listStatus === "loading" && (
        <div className="flex items-center justify-center py-12 text-slate-400">
          <Loader2 className="h-6 w-6 animate-spin" />
        </div>
      )}

      {listStatus === "error" && (
        <div className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50/60 px-4 py-3 text-sm text-red-700">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          {listError}
        </div>
      )}

      {listStatus === "done" && items.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-white py-14 text-center">
          <Inbox className="h-10 w-10 text-slate-300" />
          <p className="mt-3 text-sm font-medium text-slate-600">No submissions yet</p>
          <p className="mt-1 text-sm text-slate-400">Upload your marksheet to get started.</p>
          <Link to="/student-upload" className={buttonVariants({ variant: "primary" }) + " mt-5"}>
            Submit a marksheet
          </Link>
        </div>
      )}

      {listStatus === "done" && items.length > 0 && (
        <div className="space-y-3">
          {items.map((item) => (
            <SubmissionCard
              key={item.case_id}
              item={item}
              highlight={item.case_id === highlightId}
            />
          ))}
        </div>
      )}

      {/* Optional: look up a specific submission ID */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
          Look up a submission ID
        </p>
        <div className="flex items-end gap-2">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              value={caseId}
              onChange={(e) => setCaseId(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && lookupById()}
              placeholder="e.g. case_ab12cd34ef56"
              className="h-10 w-full rounded-lg border border-slate-200 bg-white pl-9 pr-3 font-mono text-sm text-slate-700 placeholder:font-sans placeholder:text-slate-400 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            />
          </div>
          <button
            onClick={lookupById}
            disabled={!caseId.trim() || lookupStatus === "loading"}
            className={buttonVariants({ variant: "primary" })}
          >
            {lookupStatus === "loading" ? "Checking…" : "Track"}
          </button>
        </div>

        {lookupStatus === "error" && (
          <p className="mt-3 flex items-start gap-1.5 text-sm text-red-600">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            {lookupError}
          </p>
        )}
        {lookupStatus === "done" && lookup && (
          <div className="mt-3">
            <SubmissionCard item={lookup} highlight />
          </div>
        )}
      </div>
    </div>
  );
}

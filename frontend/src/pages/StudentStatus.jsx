import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { motion } from "motion/react";
import { Search, AlertCircle, Clock, AlertTriangle } from "lucide-react";
import StatusBadge from "../components/StatusBadge";
import { getStudentSubmission } from "../api";
import { buttonVariants, formatDateTime } from "../lib/utils";

export default function StudentStatus() {
  const [searchParams] = useSearchParams();
  const [caseId, setCaseId] = useState(searchParams.get("case_id") || "");
  const [status, setStatus] = useState("idle"); // idle | loading | done | error
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  async function track(id) {
    const value = (id ?? caseId).trim();
    if (!value) return;
    setStatus("loading");
    setError("");
    setData(null);
    try {
      const res = await getStudentSubmission(value);
      setData(res);
      setStatus("done");
    } catch (err) {
      setError(err.message || "Submission not found.");
      setStatus("error");
    }
  }

  // Auto-track if a case_id was passed in the URL.
  useEffect(() => {
    const id = searchParams.get("case_id");
    if (id) track(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Track your submission</h2>
        <p className="mt-1 text-sm text-slate-500">
          Enter the submission ID you received after uploading your marksheet.
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-end gap-2">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              value={caseId}
              onChange={(e) => setCaseId(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && track()}
              placeholder="e.g. case_ab12cd34ef56"
              className="h-10 w-full rounded-lg border border-slate-200 bg-white pl-9 pr-3 font-mono text-sm text-slate-700 placeholder:font-sans placeholder:text-slate-400 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            />
          </div>
          <button
            onClick={() => track()}
            disabled={!caseId.trim() || status === "loading"}
            className={buttonVariants({ variant: "primary" })}
          >
            {status === "loading" ? "Checking…" : "Track"}
          </button>
        </div>
      </div>

      {status === "error" && (
        <div className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50/60 px-4 py-3 text-sm text-red-700">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {status === "done" && data && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="font-mono text-xs text-slate-400">{data.case_id}</p>
            <StatusBadge status={data.status} />
          </div>

          <p className="mt-3 text-sm text-slate-700">{data.message}</p>

          {data.action_required && data.action_message && (
            <div className="mt-3 flex items-start gap-2 rounded-lg bg-orange-50 px-3 py-2.5 ring-1 ring-inset ring-orange-100">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-orange-600" />
              <p className="text-sm text-orange-800">{data.action_message}</p>
            </div>
          )}

          <div className="mt-4 flex flex-wrap gap-4 text-xs text-slate-400">
            <span className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5" />
              Submitted {formatDateTime(data.submitted_at)}
            </span>
            {data.updated_at && (
              <span className="flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5" />
                Updated {formatDateTime(data.updated_at)}
              </span>
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
}

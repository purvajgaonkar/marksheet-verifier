import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Files,
  ShieldCheck,
  Search,
  AlertTriangle,
  RefreshCw,
  Upload,
  SearchX,
} from "lucide-react";
import StatCard from "../components/StatCard";
import CaseTable from "../components/CaseTable";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import { StatCardSkeleton, TableSkeleton } from "../components/Skeleton";
import { getAdminCases } from "../api";
import { buttonVariants, cn, formatDateTime } from "../lib/utils";

// Bucket helpers that work for BOTH internal labels (verified/low/...) and the
// Phase 8 admin labels (low_risk/medium_risk/high_risk_signal/...).
const _LOW = new Set(["verified", "low", "low_risk"]);
const _REVIEW = new Set(["medium", "medium_risk", "needs_review"]);
const _HIGH = new Set(["high", "high_risk_signal"]);

// Group risk labels into the four dashboard buckets.
function summarise(cases) {
  const counts = { total: cases.length, low: 0, review: 0, high: 0 };
  let ocrSum = 0;
  let ocrCount = 0;
  for (const c of cases) {
    const label = c.risk_label || c.admin_risk_label;
    if (_LOW.has(label)) counts.low += 1;
    else if (_REVIEW.has(label)) counts.review += 1;
    else if (_HIGH.has(label)) counts.high += 1;
    if (typeof c.ocr_confidence === "number") {
      ocrSum += c.ocr_confidence;
      ocrCount += 1;
    }
  }
  counts.avgOcr = ocrCount ? Math.round((ocrSum / ocrCount) * 10) / 10 : null;
  return counts;
}

// Risk filter chips (each maps to a set of backend labels).
const FILTERS = [
  { key: "all", label: "All", match: () => true },
  { key: "low", label: "Low", match: (l) => _LOW.has(l) },
  { key: "review", label: "Needs review", match: (l) => _REVIEW.has(l) },
  { key: "high", label: "High", match: (l) => _HIGH.has(l) },
];

export default function AdminDashboard() {
  const [cases, setCases] = useState([]);
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [refreshedAt, setRefreshedAt] = useState(null);

  const load = useCallback(async () => {
    setStatus("loading");
    setError("");
    try {
      const data = await getAdminCases();
      setCases(data);
      setStatus("ready");
      setRefreshedAt(new Date().toISOString());
    } catch (err) {
      setError(err.message || "Could not load cases.");
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const counts = summarise(cases);

  // Apply the risk filter + text search.
  const filtered = useMemo(() => {
    const activeFilter = FILTERS.find((f) => f.key === filter) || FILTERS[0];
    const q = query.trim().toLowerCase();
    return cases.filter((c) => {
      if (!activeFilter.match(c.risk_label)) return false;
      if (!q) return true;
      return (
        (c.filename || "").toLowerCase().includes(q) ||
        (c.case_id || "").toLowerCase().includes(q)
      );
    });
  }, [cases, filter, query]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Admin Dashboard</h2>
          <p className="mt-1 text-sm text-slate-500">
            Review uploaded marksheets and their risk signals.
            {counts.review + counts.high > 0 && (
              <span className="text-slate-400">
                {" "}· {counts.review + counts.high} case
                {counts.review + counts.high === 1 ? "" : "s"} for human review
              </span>
            )}
            {counts.avgOcr != null && (
              <span className="text-slate-400"> · Avg OCR confidence {counts.avgOcr}/100</span>
            )}
            {refreshedAt && (
              <span className="text-slate-400"> · Updated {formatDateTime(refreshedAt)}</span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={load}
            disabled={status === "loading"}
            className={buttonVariants({ variant: "secondary" })}
          >
            <RefreshCw className={cn("h-4 w-4", status === "loading" && "animate-spin")} />
            Refresh
          </button>
          <Link to="/upload" className={buttonVariants({ variant: "primary" })}>
            <Upload className="h-4 w-4" />
            Upload
          </Link>
        </div>
      </div>

      {/* Stat cards (skeleton while loading) */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {status === "loading" ? (
          Array.from({ length: 4 }).map((_, i) => <StatCardSkeleton key={i} />)
        ) : (
          <>
            <StatCard title="Total cases" value={counts.total} Icon={Files} accent="indigo" index={0} />
            <StatCard title="Low risk" value={counts.low} Icon={ShieldCheck} accent="emerald" index={1} />
            <StatCard title="Needs review" value={counts.review} Icon={Search} accent="amber" index={2} />
            <StatCard title="High risk" value={counts.high} Icon={AlertTriangle} accent="red" index={3} />
          </>
        )}
      </div>

      {/* Error */}
      {status === "error" && (
        <ErrorState
          title="Could not reach the backend"
          message={error}
          command="python -m uvicorn app.main:app --reload --app-dir backend"
          onRetry={load}
        />
      )}

      {/* Empty (no cases at all) */}
      {status === "ready" && cases.length === 0 && (
        <EmptyState
          title="No cases yet"
          message="Upload a marksheet to create the first case and see it appear here."
          action={
            <Link to="/upload" className={buttonVariants({ variant: "primary" })}>
              <Upload className="h-4 w-4" />
              Upload a marksheet
            </Link>
          }
        />
      )}

      {/* Toolbar + table */}
      {status === "ready" && cases.length > 0 && (
        <div className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            {/* Search */}
            <div className="relative w-full sm:max-w-xs">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search by filename or case ID…"
                className="h-10 w-full rounded-lg border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
              />
            </div>

            {/* Risk filter chips */}
            <div className="flex flex-wrap items-center gap-1.5">
              {FILTERS.map((f) => (
                <button
                  key={f.key}
                  onClick={() => setFilter(f.key)}
                  className={cn(
                    "rounded-full px-3 py-1.5 text-xs font-medium ring-1 ring-inset transition-colors",
                    filter === f.key
                      ? "bg-indigo-600 text-white ring-indigo-600"
                      : "bg-white text-slate-600 ring-slate-200 hover:bg-slate-50"
                  )}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          <p className="text-xs text-slate-400">
            Showing {filtered.length} of {cases.length} case{cases.length === 1 ? "" : "s"}
          </p>

          {filtered.length > 0 ? (
            <CaseTable cases={filtered} />
          ) : (
            <EmptyState
              Icon={SearchX}
              title="No matching cases"
              message="Try a different search term or clear the risk filter."
              action={
                <button
                  onClick={() => {
                    setQuery("");
                    setFilter("all");
                  }}
                  className={buttonVariants({ variant: "secondary" })}
                >
                  Clear filters
                </button>
              }
            />
          )}
        </div>
      )}

      {/* Table skeleton while loading */}
      {status === "loading" && <TableSkeleton rows={5} />}
    </div>
  );
}

import { useNavigate } from "react-router-dom";
import { motion } from "motion/react";
import { Eye } from "lucide-react";
import RiskBadge from "./RiskBadge";
import { buttonVariants, formatDateTime } from "../lib/utils";

// Friendly labels for the status field stored on each case.
const STATUS_LABELS = {
  // Phase 8 student-facing workflow statuses
  submitted: "Submitted",
  processing: "Processing",
  under_review: "Under review",
  verified: "Verified",
  reupload_required: "Re-upload required",
  official_verification_required: "Official verification required",
  closed: "Closed",
  // legacy reviewer statuses (kept for backward compatibility)
  pending_review: "Pending review",
  approved: "Approved",
  needs_more_documents: "Needs more documents",
  rejected_after_manual_review: "Rejected (manual review)",
};

function StatusText({ status }) {
  if (!status) return <span className="text-slate-400">—</span>;
  return <span className="text-slate-600">{STATUS_LABELS[status] || status}</span>;
}

/**
 * CaseTable - a responsive table listing every case. Clicking "View" (or a
 * row) opens the CaseDetail page.
 */
export default function CaseTable({ cases }) {
  const navigate = useNavigate();

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr className="text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <th className="px-4 py-3">Case ID</th>
              <th className="px-4 py-3">Filename</th>
              <th className="px-4 py-3">Uploaded</th>
              <th className="px-4 py-3">Risk</th>
              <th className="px-4 py-3 text-right">Score</th>
              <th className="px-4 py-3 text-right">OCR&nbsp;conf.</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {cases.map((c, i) => (
              <motion.tr
                key={c.case_id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.2, delay: Math.min(i * 0.03, 0.3) }}
                onClick={() => navigate(`/cases/${c.case_id}`)}
                className="cursor-pointer transition-colors hover:bg-slate-50"
              >
                <td className="px-4 py-3 font-mono text-xs text-slate-500">{c.case_id}</td>
                <td className="px-4 py-3 max-w-[200px] truncate font-medium text-slate-800">
                  {c.filename}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-slate-500">
                  {formatDateTime(c.uploaded_at)}
                </td>
                <td className="px-4 py-3">
                  <RiskBadge label={c.risk_label} size="sm" />
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                  {c.risk_score ?? "—"}
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                  {c.ocr_confidence != null ? `${c.ocr_confidence}` : "—"}
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <StatusText status={c.status} />
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/cases/${c.case_id}`);
                    }}
                    className={buttonVariants({ variant: "secondary", size: "sm" })}
                  >
                    <Eye className="h-3.5 w-3.5" />
                    View
                  </button>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

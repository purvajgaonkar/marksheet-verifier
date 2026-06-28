import {
  Inbox,
  Loader2,
  Search,
  ShieldCheck,
  RotateCcw,
  FileSearch,
  CheckCircle2,
  HelpCircle,
} from "lucide-react";
import { cn } from "../lib/utils";

// Student-facing workflow status -> friendly label + soft color + icon.
// Wording is intentionally safe (never accusatory).
const STATUS_META = {
  submitted: { label: "Submitted", cls: "bg-slate-100 text-slate-600 ring-slate-200", Icon: Inbox },
  processing: { label: "Processing", cls: "bg-indigo-50 text-indigo-700 ring-indigo-200", Icon: Loader2 },
  under_review: { label: "Under review", cls: "bg-amber-50 text-amber-700 ring-amber-200", Icon: Search },
  verified: { label: "Verified", cls: "bg-emerald-50 text-emerald-700 ring-emerald-200", Icon: ShieldCheck },
  reupload_required: { label: "Re-upload required", cls: "bg-orange-50 text-orange-700 ring-orange-200", Icon: RotateCcw },
  official_verification_required: {
    label: "Official verification required",
    cls: "bg-violet-50 text-violet-700 ring-violet-200",
    Icon: FileSearch,
  },
  closed: { label: "Closed", cls: "bg-slate-100 text-slate-600 ring-slate-200", Icon: CheckCircle2 },
};

export function getStatusMeta(status) {
  return (
    STATUS_META[status] || {
      label: status || "Unknown",
      cls: "bg-slate-100 text-slate-600 ring-slate-200",
      Icon: HelpCircle,
    }
  );
}

/** StatusBadge - a color-coded pill for a workflow status. */
export default function StatusBadge({ status, size = "md" }) {
  const meta = getStatusMeta(status);
  const { Icon } = meta;
  const sizing = size === "sm" ? "px-2 py-0.5 text-xs gap-1" : "px-2.5 py-1 text-sm gap-1.5";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full font-medium ring-1 ring-inset whitespace-nowrap",
        meta.cls,
        sizing
      )}
    >
      <Icon className={cn(size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5", status === "processing" && "animate-spin")} />
      {meta.label}
    </span>
  );
}

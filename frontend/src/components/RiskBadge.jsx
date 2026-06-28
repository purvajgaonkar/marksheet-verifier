import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  HelpCircle,
  Search,
} from "lucide-react";
import { cn } from "../lib/utils";

// ---------------------------------------------------------------------------
// Central mapping from a backend risk label to professional, non-accusatory
// wording + soft color styling + an icon. Importantly, we NEVER use words like
// "fraud", "fake", or "forged" — only neutral review signals.
// ---------------------------------------------------------------------------
export const RISK_META = {
  verified: {
    label: "Verified — no signals",
    classes: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    dot: "bg-emerald-500",
    Icon: ShieldCheck,
  },
  low: {
    label: "Low risk",
    classes: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    dot: "bg-emerald-500",
    Icon: ShieldCheck,
  },
  medium: {
    label: "Medium risk",
    classes: "bg-amber-50 text-amber-700 ring-amber-200",
    dot: "bg-amber-500",
    Icon: ShieldAlert,
  },
  needs_review: {
    label: "Needs review",
    classes: "bg-orange-50 text-orange-700 ring-orange-200",
    dot: "bg-orange-500",
    Icon: Search,
  },
  high: {
    label: "High risk signal",
    classes: "bg-red-50 text-red-700 ring-red-200",
    dot: "bg-red-500",
    Icon: AlertTriangle,
  },
  unable_to_verify: {
    label: "Unable to verify",
    classes: "bg-slate-100 text-slate-600 ring-slate-200",
    dot: "bg-slate-400",
    Icon: HelpCircle,
  },
  unknown: {
    label: "Unknown",
    classes: "bg-slate-100 text-slate-600 ring-slate-200",
    dot: "bg-slate-400",
    Icon: HelpCircle,
  },
  // Phase 8: admin-facing label aliases (stored in the database).
  low_risk: {
    label: "Low risk",
    classes: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    dot: "bg-emerald-500",
    Icon: ShieldCheck,
  },
  medium_risk: {
    label: "Medium risk",
    classes: "bg-amber-50 text-amber-700 ring-amber-200",
    dot: "bg-amber-500",
    Icon: ShieldAlert,
  },
  high_risk_signal: {
    label: "High risk signal",
    classes: "bg-red-50 text-red-700 ring-red-200",
    dot: "bg-red-500",
    Icon: AlertTriangle,
  },
};

export function getRiskMeta(label) {
  return RISK_META[label] || RISK_META.unknown;
}

/**
 * RiskBadge renders a single color-coded pill for a risk label.
 *
 * props:
 *   label  - the backend risk label (verified | low | medium | needs_review | high | unable_to_verify)
 *   size   - "sm" | "md"
 */
export default function RiskBadge({ label, size = "md" }) {
  const meta = getRiskMeta(label);
  const { Icon } = meta;
  const sizing =
    size === "sm" ? "px-2 py-0.5 text-xs gap-1" : "px-2.5 py-1 text-sm gap-1.5";

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full font-medium ring-1 ring-inset whitespace-nowrap",
        meta.classes,
        sizing
      )}
      title={meta.label}
    >
      <Icon className={size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5"} />
      {meta.label}
    </span>
  );
}

import { motion } from "motion/react";
import { cn } from "../lib/utils";

// Deliberately calm colors — this is a review aid, not a fraud alarm.
const LEVELS = {
  low: { label: "Low", bar: "bg-emerald-500", chip: "bg-emerald-50 text-emerald-700 ring-emerald-200" },
  medium: { label: "Medium", bar: "bg-amber-500", chip: "bg-amber-50 text-amber-700 ring-amber-200" },
  high: { label: "High", bar: "bg-orange-500", chip: "bg-orange-50 text-orange-700 ring-orange-200" },
};

/**
 * SignalMeter - one weak forensic signal as a labelled progress bar.
 *
 * props:
 *   name        - signal name (e.g. "ELA difference")
 *   score       - 0..1
 *   level       - "low" | "medium" | "high"
 *   explanation - short text under the bar
 */
export default function SignalMeter({ name, score = 0, level = "low", explanation }) {
  const cfg = LEVELS[level] || LEVELS.low;
  const pct = Math.round(Math.max(0, Math.min(1, score)) * 100);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-slate-800">{name}</p>
        <span className={cn("rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset", cfg.chip)}>
          {cfg.label} · {score}
        </span>
      </div>
      <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className={cn("h-full rounded-full", cfg.bar)}
        />
      </div>
      {explanation && <p className="mt-2 text-xs leading-relaxed text-slate-500">{explanation}</p>}
    </div>
  );
}

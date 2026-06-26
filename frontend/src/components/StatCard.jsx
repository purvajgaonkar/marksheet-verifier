import { motion } from "motion/react";
import { cn } from "../lib/utils";

// Soft accent palette for the icon chip. Keyed by an "accent" prop.
const ACCENTS = {
  indigo: "bg-indigo-50 text-indigo-600",
  emerald: "bg-emerald-50 text-emerald-600",
  amber: "bg-amber-50 text-amber-600",
  orange: "bg-orange-50 text-orange-600",
  red: "bg-red-50 text-red-600",
  slate: "bg-slate-100 text-slate-600",
};

/**
 * StatCard - one metric tile for the dashboard.
 *
 * props:
 *   title  - small label (e.g. "Total cases")
 *   value  - the number/string to highlight
 *   Icon   - a lucide icon component
 *   accent - color key from ACCENTS
 *   index  - position, used to stagger the entrance animation
 */
export default function StatCard({ title, value, Icon, accent = "indigo", index = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut", delay: index * 0.06 }}
      className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
    >
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{title}</p>
        {Icon && (
          <span className={cn("flex h-9 w-9 items-center justify-center rounded-lg", ACCENTS[accent])}>
            <Icon className="h-5 w-5" />
          </span>
        )}
      </div>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">{value}</p>
    </motion.div>
  );
}

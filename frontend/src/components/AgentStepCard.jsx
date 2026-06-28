import { motion } from "motion/react";
import {
  ScanText,
  Fingerprint,
  ScanSearch,
  ListChecks,
  Scale,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  MinusCircle,
  Loader2,
  Bot,
} from "lucide-react";
import { cn } from "../lib/utils";

// Icon per agent (falls back to a generic bot icon).
const AGENT_ICONS = {
  "OCR Agent": ScanText,
  "Metadata Agent": Fingerprint,
  "Forensics Agent": ScanSearch,
  "Rule Validation Agent": ListChecks,
  "Decision Agent": Scale,
};

// Status badge styling + icon. Colors stay calm and professional.
const STATUS_META = {
  completed: { label: "Completed", cls: "bg-emerald-50 text-emerald-700 ring-emerald-200", Icon: CheckCircle2 },
  completed_with_warnings: { label: "Completed · warnings", cls: "bg-amber-50 text-amber-700 ring-amber-200", Icon: AlertTriangle },
  failed: { label: "Failed", cls: "bg-red-50 text-red-700 ring-red-200", Icon: XCircle },
  skipped: { label: "Skipped", cls: "bg-slate-100 text-slate-600 ring-slate-200", Icon: MinusCircle },
  running: { label: "Running", cls: "bg-indigo-50 text-indigo-700 ring-indigo-200", Icon: Loader2 },
  pending: { label: "Pending", cls: "bg-slate-100 text-slate-500 ring-slate-200", Icon: MinusCircle },
};

function List({ items, tone }) {
  if (!items || items.length === 0) return null;
  const dot = tone === "warn" ? "bg-amber-400" : tone === "error" ? "bg-red-400" : "bg-slate-300";
  const text = tone === "warn" ? "text-amber-700" : tone === "error" ? "text-red-700" : "text-slate-600";
  return (
    <ul className="mt-1 space-y-1">
      {items.map((it, i) => (
        <li key={i} className={cn("flex items-start gap-2 text-xs", text)}>
          <span className={cn("mt-1.5 h-1 w-1 shrink-0 rounded-full", dot)} />
          {it}
        </li>
      ))}
    </ul>
  );
}

/**
 * AgentStepCard - one agent's result in the workflow trace.
 *
 * props:
 *   agent - a trace entry { agent_name, status, duration_ms, summary,
 *           findings, warnings, errors, confidence }
 *   index - position, used to stagger the entrance animation
 *   isLast - hide the connector line on the final card
 */
export default function AgentStepCard({ agent, index = 0, isLast = false }) {
  const Icon = AGENT_ICONS[agent.agent_name] || Bot;
  const status = STATUS_META[agent.status] || STATUS_META.completed;
  const StatusIcon = status.Icon;

  return (
    <div className="relative pl-10">
      {/* Timeline node + connector */}
      <span className="absolute left-0 top-1 flex h-7 w-7 items-center justify-center rounded-full bg-indigo-50 text-indigo-600 ring-1 ring-indigo-100">
        <Icon className="h-4 w-4" />
      </span>
      {!isLast && <span className="absolute left-[13px] top-9 bottom-0 w-px bg-slate-200" />}

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, delay: index * 0.05 }}
        className="mb-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold text-slate-900">{agent.agent_name}</h4>
            {typeof agent.duration_ms === "number" && (
              <span className="text-xs text-slate-400">{agent.duration_ms} ms</span>
            )}
          </div>
          <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset", status.cls)}>
            <StatusIcon className={cn("h-3.5 w-3.5", agent.status === "running" && "animate-spin")} />
            {status.label}
          </span>
        </div>

        {agent.summary && <p className="mt-1.5 text-sm text-slate-600">{agent.summary}</p>}

        {agent.findings?.length > 0 && (
          <div className="mt-3">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Findings</p>
            <List items={agent.findings} tone="finding" />
          </div>
        )}

        {agent.warnings?.length > 0 && (
          <div className="mt-2">
            <p className="text-xs font-medium uppercase tracking-wide text-amber-500">Warnings</p>
            <List items={agent.warnings} tone="warn" />
          </div>
        )}

        {agent.errors?.length > 0 && (
          <div className="mt-2">
            <p className="text-xs font-medium uppercase tracking-wide text-red-500">Errors</p>
            <List items={agent.errors} tone="error" />
          </div>
        )}
      </motion.div>
    </div>
  );
}

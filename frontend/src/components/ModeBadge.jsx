import { Sparkles, Cpu, AlertTriangle } from "lucide-react";
import { cn } from "../lib/utils";

// Maps an answer "mode" to a friendly, professional badge (Phase 7).
const MODE_META = {
  claude_rag: {
    label: "Claude-powered RAG",
    cls: "bg-indigo-50 text-indigo-700 ring-indigo-200",
    Icon: Sparkles,
  },
  local_retrieval_template: {
    label: "Local fallback",
    cls: "bg-slate-100 text-slate-600 ring-slate-200",
    Icon: Cpu,
  },
  local_retrieval_template_fallback: {
    label: "Local fallback (LLM unavailable)",
    cls: "bg-amber-50 text-amber-700 ring-amber-200",
    Icon: AlertTriangle,
  },
};

/**
 * ModeBadge - shows which engine produced an answer, plus the model name when
 * Claude was used.
 *
 * props: mode (string), model (string|null)
 */
export default function ModeBadge({ mode, model }) {
  const meta = MODE_META[mode] || MODE_META.local_retrieval_template;
  const { Icon } = meta;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset",
        meta.cls
      )}
      title={mode}
    >
      <Icon className="h-3.5 w-3.5" />
      {meta.label}
      {model ? <span className="font-mono opacity-70">· {model}</span> : null}
    </span>
  );
}

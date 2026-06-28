import { Workflow, Cpu, Clock, Hash, UserCheck, ShieldCheck } from "lucide-react";
import ReportSection from "./ReportSection";
import AgentStepCard from "./AgentStepCard";
import { cn } from "../lib/utils";

/**
 * AgentTracePanel - shows the Phase 5 "Agentic Workflow Trace": the local
 * rule-based agents that produced the report, with a per-agent timeline and the
 * final human-review recommendation.
 *
 * props:
 *   workflow - report.agentic_workflow (or undefined on older reports)
 */
export default function AgentTracePanel({ workflow }) {
  // Backward compatibility: older reports have no agentic workflow.
  if (!workflow || workflow.available === false) {
    return (
      <ReportSection title="Agentic Workflow Trace" Icon={Workflow}>
        <p className="text-sm text-slate-500">
          Agent trace is not available for this older report. Re-upload the document
          to run the local rule-based agents.
        </p>
      </ReportSection>
    );
  }

  const trace = workflow.trace || [];
  const reco = workflow.recommendation || {};
  const humanReview = reco.human_review_required;

  const meta = [
    { Icon: Cpu, label: "Mode", value: workflow.mode || "local_rule_based" },
    { Icon: Hash, label: "Run ID", value: workflow.run_id || "—", mono: true },
    { Icon: Workflow, label: "Agents", value: workflow.agents_executed ?? trace.length },
    { Icon: Clock, label: "Duration", value: workflow.duration_ms != null ? `${workflow.duration_ms} ms` : "—" },
  ];

  return (
    <ReportSection title="Agentic Workflow Trace" Icon={Workflow}>
      {/* Workflow meta */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {meta.map((m) => (
          <div key={m.label} className="rounded-lg bg-slate-50 px-4 py-3">
            <div className="flex items-center gap-1.5 text-slate-400">
              <m.Icon className="h-3.5 w-3.5" />
              <span className="text-xs font-medium uppercase tracking-wide">{m.label}</span>
            </div>
            <p className={cn("mt-1 truncate text-sm font-semibold text-slate-800", m.mono && "font-mono text-xs")}>
              {m.value}
            </p>
          </div>
        ))}
      </div>

      <p className="mt-3 text-xs text-slate-400">
        Local rule-based agents — evidence aggregation only. No external AI/LLM API is used.
      </p>

      {/* Human review recommendation */}
      {reco.recommendation && (
        <div
          className={cn(
            "mt-4 flex items-start gap-3 rounded-xl px-5 py-4 ring-1 ring-inset",
            humanReview
              ? "bg-amber-50 text-amber-800 ring-amber-200"
              : "bg-emerald-50 text-emerald-800 ring-emerald-200"
          )}
        >
          {humanReview ? (
            <UserCheck className="mt-0.5 h-5 w-5 shrink-0" />
          ) : (
            <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0" />
          )}
          <div>
            <p className="text-sm font-semibold">
              Human review recommendation:{" "}
              {humanReview ? "Manual review recommended" : "No manual review required"}
            </p>
            <p className="mt-0.5 text-sm opacity-90">{reco.recommendation}</p>
          </div>
        </div>
      )}

      {/* Agent timeline */}
      <div className="mt-6">
        <h4 className="mb-3 text-sm font-semibold text-slate-900">Evidence aggregation timeline</h4>
        {trace.map((agent, i) => (
          <AgentStepCard
            key={`${agent.agent_name}-${i}`}
            agent={agent}
            index={i}
            isLast={i === trace.length - 1}
          />
        ))}
      </div>

      <p className="mt-2 text-xs text-slate-400">
        {reco.important_note || "This is an MVP signal report, not final proof of tampering."}
      </p>
    </ReportSection>
  );
}

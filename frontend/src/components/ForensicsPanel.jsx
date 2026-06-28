import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { ScanSearch, Info, AlertTriangle } from "lucide-react";
import ReportSection from "./ReportSection";
import SignalMeter from "./SignalMeter";
import ForensicsImageCard from "./ForensicsImageCard";
import { getForensics } from "../api";
import { cn } from "../lib/utils";

// Professional captions for each forensic output image.
const IMAGE_META = [
  { key: "normalized_image", title: "Normalized Document", caption: "Clean copy used for all forensic steps." },
  { key: "anomaly_heatmap", title: "Anomaly Heatmap", caption: "Combined weak signals overlaid on the page." },
  { key: "ela_image", title: "ELA-style Difference View", caption: "Highlights areas that recompress differently." },
  { key: "edge_map", title: "Edge Map", caption: "Canny edges (informational context)." },
  { key: "sharpness_map", title: "Sharpness Map", caption: "Local sharpness energy across the page." },
  { key: "noise_map", title: "Noise Map", caption: "Local high-frequency noise across the page." },
];

function anomalyLevel(score) {
  if (score < 0.34) return { label: "Low", chip: "bg-emerald-50 text-emerald-700 ring-emerald-200", bar: "bg-emerald-500" };
  if (score < 0.67) return { label: "Medium", chip: "bg-amber-50 text-amber-700 ring-amber-200", bar: "bg-amber-500" };
  return { label: "High", chip: "bg-orange-50 text-orange-700 ring-orange-200", bar: "bg-orange-500" };
}

export default function ForensicsPanel({ forensics, caseId }) {
  const [imageUrls, setImageUrls] = useState({});

  useEffect(() => {
    let active = true;
    if (forensics && forensics.available) {
      getForensics(caseId)
        .then((res) => active && setImageUrls(res.outputs || {}))
        .catch(() => active && setImageUrls({}));
    }
    return () => {
      active = false;
    };
  }, [caseId, forensics]);

  // --- Backward compatibility: older reports have no image_forensics. -----
  if (!forensics) {
    return (
      <ReportSection title="Image Forensics Signals" Icon={ScanSearch}>
        <p className="text-sm text-slate-500">
          Image forensics is not available for this older report. Re-upload the
          document to generate forensic signals.
        </p>
      </ReportSection>
    );
  }

  // --- Forensics ran but failed. -----------------------------------------
  if (!forensics.available) {
    return (
      <ReportSection title="Image Forensics Signals" Icon={ScanSearch}>
        <div className="flex items-start gap-3 rounded-lg bg-slate-50 px-4 py-3">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-slate-400" />
          <div>
            <p className="text-sm font-medium text-slate-700">
              {forensics.summary || "Image forensics could not be generated."}
            </p>
            {forensics.error && (
              <p className="mt-0.5 text-xs text-slate-500">{forensics.error}</p>
            )}
          </div>
        </div>
      </ReportSection>
    );
  }

  const score = forensics.anomaly_score ?? 0;
  const lvl = anomalyLevel(score);
  const pct = Math.round(Math.max(0, Math.min(1, score)) * 100);
  const signals = forensics.signals || [];
  const limitations = forensics.limitations || [];

  return (
    <ReportSection title="Image Forensics Signals" Icon={ScanSearch}>
      {/* Anomaly score + summary */}
      <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
              Combined anomaly score
            </p>
            <div className="mt-1 flex items-center gap-2">
              <span className="text-2xl font-bold tabular-nums text-slate-900">{score}</span>
              <span className={cn("rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset", lvl.chip)}>
                {lvl.label}
              </span>
            </div>
          </div>
          <p className="max-w-md text-sm text-slate-600">{forensics.summary}</p>
        </div>
        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-200">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.7, ease: "easeOut" }}
            className={cn("h-full rounded-full", lvl.bar)}
          />
        </div>
      </div>

      {/* Weak-evidence disclaimer */}
      <div className="mt-4 flex items-start gap-2.5 rounded-lg border border-indigo-100 bg-indigo-50/60 px-4 py-3">
        <Info className="mt-0.5 h-4.5 w-4.5 shrink-0 text-indigo-600" style={{ height: 18, width: 18 }} />
        <p className="text-sm text-slate-700">
          These visualizations are review aids only and do not prove document tampering.
          Compression, scanning, mobile capture, and PDF conversion can all create false
          positives — manual review and official verification are required.
        </p>
      </div>

      {/* Signal meters */}
      {signals.length > 0 && (
        <div className="mt-5">
          <h4 className="text-sm font-semibold text-slate-900">Weak signals</h4>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {signals.map((s) => (
              <SignalMeter
                key={s.name}
                name={s.name}
                score={s.score}
                level={s.level}
                explanation={s.explanation}
              />
            ))}
          </div>
        </div>
      )}

      {/* Forensic images */}
      <div className="mt-6">
        <h4 className="text-sm font-semibold text-slate-900">Forensic visualizations</h4>
        <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {IMAGE_META.map((m) => (
            <ForensicsImageCard
              key={m.key}
              title={m.title}
              caption={m.caption}
              src={imageUrls[m.key]}
            />
          ))}
        </div>
      </div>

      {/* Limitations */}
      {limitations.length > 0 && (
        <div className="mt-6 rounded-lg bg-slate-50 px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Limitations of pixel forensics
          </p>
          <ul className="mt-2 space-y-1">
            {limitations.map((l, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-slate-500">
                <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-slate-400" />
                {l}
              </li>
            ))}
          </ul>
        </div>
      )}
    </ReportSection>
  );
}

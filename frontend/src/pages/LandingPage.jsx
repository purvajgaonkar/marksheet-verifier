import { Link } from "react-router-dom";
import { motion } from "motion/react";
import {
  ScanText,
  Fingerprint,
  ShieldAlert,
  ShieldCheck,
  Upload,
  LayoutDashboard,
  Info,
  ArrowRight,
  FileSearch,
  UserCheck,
  Check,
} from "lucide-react";
import { buttonVariants } from "../lib/utils";
import { useAuth } from "../context/AuthContext";

// Route the hero CTAs by the current auth state / role (Phase 9).
function ctaTargets(user) {
  if (!user) {
    return {
      primary: { to: "/register", label: "Get started" },
      secondary: { to: "/login", label: "Sign in" },
    };
  }
  if (user.role === "student") {
    return {
      primary: { to: "/student-upload", label: "Upload Marksheet" },
      secondary: { to: "/track", label: "Track My Submissions" },
    };
  }
  return {
    primary: { to: "/admin", label: "Open Admin Dashboard" },
    secondary: { to: "/assistant", label: "Policy Assistant" },
  };
}

const FEATURES = [
  {
    Icon: ScanText,
    title: "OCR Extraction",
    body: "Reads text from the marksheet with Tesseract and reports an OCR confidence score.",
    points: ["Full text extraction", "Per-document confidence", "Field detection"],
  },
  {
    Icon: Fingerprint,
    title: "Metadata Analysis",
    body: "Inspects file metadata for editor traces and date inconsistencies as neutral warnings.",
    points: ["Editor signatures", "Date mismatches", "Producer checks"],
  },
  {
    Icon: ShieldAlert,
    title: "Risk Signal Report",
    body: "Combines the signals into a transparent risk score to help reviewers prioritise.",
    points: ["Explainable score", "Clear risk label", "Never auto-rejects"],
  },
];

const STEPS = [
  { Icon: Upload, title: "Upload document", body: "Submit a PDF, JPG, or PNG marksheet." },
  { Icon: FileSearch, title: "Automated analysis", body: "OCR, metadata, and risk signals run instantly." },
  { Icon: UserCheck, title: "Human review", body: "A reviewer makes the final, informed decision." },
];

// A small reusable fade-up wrapper for staggered entrances.
function FadeUp({ delay = 0, children, className }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut", delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// A decorative, non-interactive "report preview" shown in the hero.
function ReportPreview() {
  const rows = [
    { label: "OCR confidence", value: "89 / 100" },
    { label: "Detected board", value: "CBSE" },
    { label: "Metadata warnings", value: "0" },
  ];
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xl shadow-slate-900/5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
            <FileSearch className="h-4 w-4" />
          </span>
          <p className="text-sm font-semibold text-slate-800">Verification Report</p>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-200">
          <ShieldCheck className="h-3.5 w-3.5" />
          Low risk
        </span>
      </div>

      {/* Risk meter */}
      <div className="mt-5">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>Risk score</span>
          <span className="font-medium text-slate-600">0.08</span>
        </div>
        <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-slate-100">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: "8%" }}
            transition={{ duration: 0.9, delay: 0.4, ease: "easeOut" }}
            className="h-full rounded-full bg-emerald-500"
          />
        </div>
      </div>

      <div className="mt-5 space-y-2.5">
        {rows.map((r) => (
          <div key={r.label} className="flex items-center justify-between text-sm">
            <span className="text-slate-500">{r.label}</span>
            <span className="font-medium text-slate-800">{r.value}</span>
          </div>
        ))}
      </div>

      <p className="mt-5 border-t border-slate-100 pt-3 text-[11px] text-slate-400">
        MVP signal report — not final proof of tampering.
      </p>
    </div>
  );
}

export default function LandingPage() {
  const { user } = useAuth();
  const cta = ctaTargets(user);
  return (
    <div className="space-y-14">
      {/* Hero */}
      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-gradient-to-br from-white via-white to-indigo-50 px-6 py-10 md:px-10 md:py-14">
        <div className="grid items-center gap-10 lg:grid-cols-2">
          {/* Left: copy + CTAs */}
          <div>
            <FadeUp>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-100 px-3 py-1 text-xs font-medium text-indigo-700">
                <ShieldAlert className="h-3.5 w-3.5" />
                MVP signal report — not final proof of tampering
              </span>
            </FadeUp>

            <FadeUp delay={0.06}>
              <h1 className="mt-5 text-3xl font-bold tracking-tight text-slate-900 md:text-[2.5rem] md:leading-[1.1]">
                Verify academic marksheets with confidence
              </h1>
            </FadeUp>

            <FadeUp delay={0.12}>
              <p className="mt-4 max-w-xl text-base text-slate-600 md:text-lg">
                AI-assisted academic document verification and tampering signal analysis.
                Extract text, inspect metadata, and generate an evidence-based risk signal
                for human reviewers.
              </p>
            </FadeUp>

            <FadeUp delay={0.18}>
              <div className="mt-7 flex flex-wrap gap-3">
                <Link to={cta.primary.to} className={buttonVariants({ variant: "primary", size: "lg" })}>
                  <Upload className="h-5 w-5" />
                  {cta.primary.label}
                </Link>
                <Link to={cta.secondary.to} className={buttonVariants({ variant: "secondary", size: "lg" })}>
                  <LayoutDashboard className="h-5 w-5" />
                  {cta.secondary.label}
                </Link>
              </div>
            </FadeUp>
          </div>

          {/* Right: report preview */}
          <FadeUp delay={0.2} className="hidden lg:block">
            <ReportPreview />
          </FadeUp>
        </div>
      </section>

      {/* Process stepper */}
      <section>
        <h2 className="text-lg font-semibold text-slate-900">A clear, three-step workflow</h2>
        <p className="mt-1 text-sm text-slate-500">
          The system assists reviewers — it never decides on its own.
        </p>
        <div className="mt-6 grid gap-5 sm:grid-cols-3">
          {STEPS.map((s, i) => (
            <FadeUp key={s.title} delay={0.1 + i * 0.08}>
              <div className="relative h-full rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
                    <s.Icon className="h-5 w-5" />
                  </span>
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Step {i + 1}
                  </span>
                </div>
                <h3 className="mt-4 text-base font-semibold text-slate-900">{s.title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-slate-600">{s.body}</p>
              </div>
            </FadeUp>
          ))}
        </div>
      </section>

      {/* Features */}
      <section>
        <h2 className="text-lg font-semibold text-slate-900">Three independent signals, one report</h2>
        <p className="mt-1 text-sm text-slate-500">
          Each signal is transparent and explainable.
        </p>
        <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <FadeUp key={f.title} delay={0.1 + i * 0.08}>
              <div className="h-full rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
                <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
                  <f.Icon className="h-6 w-6" />
                </span>
                <h3 className="mt-4 text-base font-semibold text-slate-900">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{f.body}</p>
                <ul className="mt-4 space-y-1.5">
                  {f.points.map((p) => (
                    <li key={p} className="flex items-center gap-2 text-sm text-slate-600">
                      <Check className="h-4 w-4 shrink-0 text-indigo-500" />
                      {p}
                    </li>
                  ))}
                </ul>
              </div>
            </FadeUp>
          ))}
        </div>
      </section>

      {/* Ethics note */}
      <FadeUp delay={0.05}>
        <section className="flex items-start gap-3 rounded-xl border border-indigo-100 bg-indigo-50/60 px-5 py-4">
          <Info className="mt-0.5 h-5 w-5 shrink-0 text-indigo-600" />
          <div>
            <p className="text-sm font-medium text-slate-800">A note on responsible use</p>
            <p className="mt-0.5 text-sm text-slate-600">
              This system generates review signals only. Final decisions require human
              verification. Metadata and pixel signals can be misleading, and official
              board verification is always stronger than image analysis.
            </p>
            <Link
              to={cta.primary.to}
              className="mt-2 inline-flex items-center gap-1 text-sm font-medium text-indigo-700 hover:text-indigo-800"
            >
              {cta.primary.label} <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>
      </FadeUp>

      {/* Footer */}
      <footer className="border-t border-slate-200 pt-6 pb-2">
        <div className="flex flex-col items-center justify-between gap-2 text-xs text-slate-400 sm:flex-row">
          <p>Marksheet Verifier · University project MVP</p>
          <p>Risk signals only · Human review required</p>
        </div>
      </footer>
    </div>
  );
}

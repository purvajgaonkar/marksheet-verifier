import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * cn() merges Tailwind class names intelligently: clsx handles conditional
 * classes, and tailwind-merge removes conflicting duplicates (e.g. if two
 * "px-*" classes are passed, the last one wins).
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

/**
 * buttonVariants() returns a Tailwind class string for our shadcn-style
 * buttons. Using a small helper keeps button styling consistent everywhere
 * without needing a separate component file.
 */
export function buttonVariants({ variant = "primary", size = "md" } = {}) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors " +
    "focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 " +
    "disabled:opacity-50 disabled:pointer-events-none select-none";

  const variants = {
    primary: "bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm",
    secondary:
      "bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 shadow-sm",
    outline:
      "bg-white text-indigo-700 border border-indigo-200 hover:bg-indigo-50",
    ghost: "text-slate-600 hover:bg-slate-100",
    danger: "bg-red-600 text-white hover:bg-red-700 shadow-sm",
    success: "bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm",
  };

  const sizes = {
    sm: "h-8 px-3 text-sm",
    md: "h-10 px-4 text-sm",
    lg: "h-12 px-6 text-base",
  };

  return cn(base, variants[variant], sizes[size]);
}

/** Format an ISO timestamp into a short, readable local string. */
export function formatDateTime(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

import { cn } from "../lib/utils";

/**
 * Skeleton - a soft, pulsing placeholder shown while data loads. Using
 * skeletons (instead of only a spinner) makes the app feel faster and more
 * professional because the layout appears instantly.
 */
export function Skeleton({ className }) {
  return <div className={cn("animate-pulse rounded-md bg-slate-200/70", className)} />;
}

/** A skeleton shaped like one dashboard stat card. */
export function StatCardSkeleton() {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-9 w-9 rounded-lg" />
      </div>
      <Skeleton className="mt-4 h-8 w-16" />
    </div>
  );
}

/** A skeleton shaped like the cases table (header + a few rows). */
export function TableSkeleton({ rows = 5 }) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
        <Skeleton className="h-3.5 w-40" />
      </div>
      <div className="divide-y divide-slate-100">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex items-center gap-4 px-4 py-4">
            <Skeleton className="h-3.5 w-28" />
            <Skeleton className="h-3.5 flex-1" />
            <Skeleton className="h-6 w-24 rounded-full" />
            <Skeleton className="h-3.5 w-10" />
            <Skeleton className="h-8 w-16 rounded-lg" />
          </div>
        ))}
      </div>
    </div>
  );
}

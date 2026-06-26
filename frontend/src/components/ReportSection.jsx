import { cn } from "../lib/utils";

/**
 * ReportSection - a titled "card" wrapper used to group blocks on the
 * CaseDetail page (e.g. Detected Fields, Metadata, OCR Text).
 *
 * props:
 *   title      - section heading
 *   Icon       - optional lucide icon shown next to the title
 *   children   - the section content
 *   className  - extra classes for the outer card
 *   action     - optional node rendered on the right of the header
 */
export default function ReportSection({ title, Icon, children, className, action }) {
  return (
    <section className={cn("rounded-xl border border-slate-200 bg-white shadow-sm", className)}>
      <div className="flex items-center justify-between gap-3 border-b border-slate-100 px-5 py-3.5">
        <div className="flex items-center gap-2">
          {Icon && <Icon className="h-4.5 w-4.5 text-indigo-600" style={{ height: 18, width: 18 }} />}
          <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
        </div>
        {action}
      </div>
      <div className="px-5 py-4">{children}</div>
    </section>
  );
}

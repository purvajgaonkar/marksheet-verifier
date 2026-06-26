import { Inbox } from "lucide-react";

/**
 * EmptyState - shown when there is no data yet (e.g. no cases uploaded).
 *
 * props:
 *   title, message - text to show
 *   Icon           - optional lucide icon (defaults to Inbox)
 *   action         - optional React node (e.g. a button/link)
 */
export default function EmptyState({ title = "Nothing here yet", message, Icon = Inbox, action }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-white py-16 px-6 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400">
        <Icon className="h-6 w-6" />
      </span>
      <h3 className="mt-4 text-base font-semibold text-slate-900">{title}</h3>
      {message && <p className="mt-1 max-w-sm text-sm text-slate-500">{message}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

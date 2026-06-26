import { AlertCircle, RefreshCw, Terminal } from "lucide-react";
import { buttonVariants } from "../lib/utils";

/**
 * ErrorState - shown when something fails (e.g. the backend is offline).
 *
 * props:
 *   title, message - text to show
 *   command        - optional shell command to help the user recover
 *   onRetry        - optional callback; if provided, a Retry button appears
 */
export default function ErrorState({
  title = "Something went wrong",
  message = "Please try again.",
  command,
  onRetry,
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-red-200 bg-red-50/50 py-14 px-6 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-red-100 text-red-600">
        <AlertCircle className="h-6 w-6" />
      </span>
      <h3 className="mt-4 text-base font-semibold text-slate-900">{title}</h3>
      <p className="mt-1 max-w-md text-sm text-slate-600">{message}</p>

      {command && (
        <div className="mt-4 w-full max-w-md text-left">
          <p className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-slate-500">
            <Terminal className="h-3.5 w-3.5" />
            Start the backend, then retry:
          </p>
          <pre className="overflow-x-auto rounded-lg bg-slate-900 px-4 py-3 text-xs text-slate-100">
            {command}
          </pre>
        </div>
      )}

      {onRetry && (
        <button onClick={onRetry} className={buttonVariants({ variant: "secondary" }) + " mt-5"}>
          <RefreshCw className="h-4 w-4" />
          Retry
        </button>
      )}
    </div>
  );
}

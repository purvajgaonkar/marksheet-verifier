import { Loader2 } from "lucide-react";

/** A centered spinner with an optional message. */
export default function LoadingState({ message = "Loading…" }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      <p className="mt-4 text-sm font-medium text-slate-500">{message}</p>
    </div>
  );
}

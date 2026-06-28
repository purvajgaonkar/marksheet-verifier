import { useState } from "react";
import { ImageOff, ImageIcon } from "lucide-react";

/**
 * ForensicsImageCard - shows one forensic output image with a title and a
 * short caption. Handles the "still loading" and "failed to load" cases so a
 * missing image never breaks the page.
 *
 * props:
 *   title    - heading (e.g. "Anomaly Heatmap")
 *   caption  - short description under the title
 *   src      - image URL (or null/undefined if not available)
 */
export default function ForensicsImageCard({ title, caption, src }) {
  const [state, setState] = useState(src ? "loading" : "missing"); // loading | loaded | error | missing

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-4 py-2.5">
        <p className="text-sm font-semibold text-slate-800">{title}</p>
        {caption && <p className="mt-0.5 text-xs text-slate-500">{caption}</p>}
      </div>

      <div className="relative flex aspect-[4/3] items-center justify-center bg-slate-50">
        {state === "missing" || state === "error" ? (
          <div className="flex flex-col items-center text-slate-400">
            <ImageOff className="h-7 w-7" />
            <p className="mt-2 text-xs">Image not available</p>
          </div>
        ) : (
          <>
            {state === "loading" && (
              <div className="absolute inset-0 flex animate-pulse items-center justify-center text-slate-300">
                <ImageIcon className="h-7 w-7" />
              </div>
            )}
            <img
              src={src}
              alt={title}
              loading="lazy"
              onLoad={() => setState("loaded")}
              onError={() => setState("error")}
              className="max-h-full max-w-full object-contain"
            />
          </>
        )}
      </div>
    </div>
  );
}

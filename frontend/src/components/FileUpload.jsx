import { useRef, useState } from "react";
import { UploadCloud, FileText, X } from "lucide-react";
import { cn } from "../lib/utils";

const ACCEPTED = [".pdf", ".jpg", ".jpeg", ".png"];

function isAccepted(file) {
  const name = (file?.name || "").toLowerCase();
  return ACCEPTED.some((ext) => name.endsWith(ext));
}

function prettySize(bytes) {
  if (!bytes && bytes !== 0) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * FileUpload - a large drag-and-drop card with a click-to-browse fallback.
 *
 * props:
 *   selectedFile - the currently chosen File (or null)
 *   onSelect     - called with a File when one is chosen/dropped
 *   onClear      - called to clear the selection
 *   disabled     - disables interaction (e.g. while uploading)
 */
export default function FileUpload({ selectedFile, onSelect, onClear, disabled }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [localError, setLocalError] = useState("");

  function handleFiles(fileList) {
    const file = fileList && fileList[0];
    if (!file) return;
    if (!isAccepted(file)) {
      setLocalError("Unsupported file type. Please choose a PDF, JPG, JPEG, or PNG.");
      return;
    }
    setLocalError("");
    onSelect(file);
  }

  function onDrop(e) {
    e.preventDefault();
    setDragging(false);
    if (disabled) return;
    handleFiles(e.dataTransfer.files);
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && !disabled && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={cn(
          "flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors",
          disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer",
          dragging
            ? "border-indigo-400 bg-indigo-50"
            : "border-slate-300 bg-slate-50 hover:border-indigo-300 hover:bg-indigo-50/40"
        )}
      >
        <span className="flex h-14 w-14 items-center justify-center rounded-full bg-indigo-100 text-indigo-600">
          <UploadCloud className="h-7 w-7" />
        </span>
        <p className="mt-4 text-sm font-medium text-slate-700">
          Drag &amp; drop your marksheet here, or{" "}
          <span className="text-indigo-600">browse files</span>
        </p>
        <p className="mt-1 text-xs text-slate-400">Supported: PDF, JPG, JPEG, PNG</p>

        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          className="hidden"
          disabled={disabled}
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {localError && <p className="mt-2 text-sm text-red-600">{localError}</p>}

      {/* Selected file preview */}
      {selectedFile && (
        <div className="mt-4 flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3">
          <div className="flex items-center gap-3 min-w-0">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
              <FileText className="h-5 w-5" />
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-slate-800">{selectedFile.name}</p>
              <p className="text-xs text-slate-400">{prettySize(selectedFile.size)}</p>
            </div>
          </div>
          {!disabled && (
            <button
              onClick={onClear}
              className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
              aria-label="Remove selected file"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      )}
    </div>
  );
}

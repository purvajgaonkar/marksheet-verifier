// ---------------------------------------------------------------------------
// api.js
// ---------------------------------------------------------------------------
// Thin wrapper around the FastAPI backend. Every function returns a Promise
// and throws an Error with a readable message when the backend responds badly,
// so the UI can show a clean ErrorState instead of a blank screen.
// ---------------------------------------------------------------------------

export const API_BASE_URL = "http://127.0.0.1:8000";

/**
 * Try to pull a useful error message out of a failed response.
 * FastAPI returns errors as { "detail": "..." }.
 */
async function readError(response) {
  try {
    const data = await response.json();
    if (data && data.detail) {
      // detail can be a string or an array of validation errors.
      if (typeof data.detail === "string") return data.detail;
      return JSON.stringify(data.detail);
    }
  } catch {
    /* response had no JSON body */
  }
  return `Request failed (HTTP ${response.status})`;
}

/** GET /health -> { status, tesseract_available, exiftool_available, ... } */
export async function getHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

/**
 * POST /upload (multipart form-data with a single "file" field).
 * Returns { case_id, filename, risk_score, risk_label, ocr_confidence, report_path, disclaimer }.
 */
export async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

/**
 * GET /cases -> the backend returns { count, cases: [...] }.
 * We return just the array of cases for convenience.
 */
export async function getCases() {
  const response = await fetch(`${API_BASE_URL}/cases`);
  if (!response.ok) throw new Error(await readError(response));
  const data = await response.json();
  return Array.isArray(data) ? data : data.cases ?? [];
}

/** GET /reports/{caseId} -> the full report object. */
export async function getReport(caseId) {
  const response = await fetch(`${API_BASE_URL}/reports/${encodeURIComponent(caseId)}`);
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

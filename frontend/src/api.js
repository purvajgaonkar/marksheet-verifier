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

/**
 * GET /forensics/{caseId} -> the available forensic image URLs for a case.
 * Returns { case_id, available, outputs: { ela_image: <url>, ... } }.
 */
export async function getForensics(caseId) {
  const response = await fetch(`${API_BASE_URL}/forensics/${encodeURIComponent(caseId)}`);
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

/**
 * POST /rag/ask -> ask the local Policy Assistant a question (optionally about
 * a specific case). Returns { question, answer, sources, case_summary, mode,
 * limitations }.
 */
export async function askPolicyAssistant(question, caseId) {
  const body = { question };
  if (caseId) body.case_id = caseId;
  const response = await fetch(`${API_BASE_URL}/rag/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

/** GET /rag/sources -> { documents, chunk_count, mode }. */
export async function getRagSources() {
  const response = await fetch(`${API_BASE_URL}/rag/sources`);
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

/** POST /rag/reindex -> rebuild the local index from docs/. */
export async function reindexRag() {
  const response = await fetch(`${API_BASE_URL}/rag/reindex`, { method: "POST" });
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

/**
 * GET /rag/llm-status -> { llm_enabled, api_key_configured, model, mode } (Phase 7).
 * Reports whether the optional Claude API mode is active. Never returns the key.
 */
export async function getLlmStatus() {
  const response = await fetch(`${API_BASE_URL}/rag/llm-status`);
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

/**
 * POST /cases/{caseId}/explain -> a source-grounded explanation of a case (Phase 7).
 * Uses Claude when enabled, otherwise the local fallback. Returns
 * { case_id, mode, model, explanation, sources, limitations, llm_available, llm_error }.
 */
export async function generateCaseExplanation(caseId) {
  const response = await fetch(
    `${API_BASE_URL}/cases/${encodeURIComponent(caseId)}/explain`,
    { method: "POST" }
  );
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

/**
 * GET /cases/{caseId}/agent-trace -> the agentic_workflow section for a case
 * (Phase 5). For older reports it returns { available: false, message }.
 * The CaseDetail page already has this data from the full report, so this is
 * provided mainly for the dedicated endpoint / standalone use.
 */
export async function getAgentTrace(caseId) {
  const response = await fetch(`${API_BASE_URL}/cases/${encodeURIComponent(caseId)}/agent-trace`);
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

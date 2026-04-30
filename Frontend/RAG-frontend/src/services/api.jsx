import config from "../config/config";

export async function pingBackend() {
  const response = await fetch(`${config.API_BASE_URL}/health`, {
    credentials: "include",
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}
// ─── Search ──────────────────────────────────────────────────────────────────

export async function searchPapers(queryData) {
  const response = await fetch(`${config.API_BASE_URL}/search`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(queryData),
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(queryData),
  });
  if (!response.ok) throw new Error("API request failed");
  return response.json();
}

// ─── Chat ─────────────────────────────────────────────────────────────────────

/**
 * Send a message to the /chat endpoint.
 *
 * The backend accepts multipart/form-data — NOT JSON — because the route
 * uses FastAPI Form() fields (and optionally a file upload).
 * We therefore build a FormData object rather than JSON.stringify().
 *
 * @param {Object} opts
 * @param {string}      opts.message    - The user's question (may include injected paper context)
 * @param {string|null} opts.sessionId  - null on the first turn; use the returned value afterwards
 * @param {number}      opts.topK       - How many papers to retrieve as context (default 5)
 * @returns {Promise<{ session_id: string, answer: string, papers: Paper[] }>}
 */
export async function chatWithPaper({ message, sessionId = null, topK = 5 }) {
  const formData = new FormData();
  formData.append("message", message);
  formData.append("top_k", String(topK));
  if (sessionId) formData.append("session_id", sessionId);

  const response = await fetch(`${config.API_BASE_URL}/chat`, {
    method: "POST",
    // ⚠️  Do NOT set Content-Type manually — the browser sets it automatically
    //     with the correct multipart boundary when you pass a FormData body.
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || "Chat request failed");
  }

  return response.json();
}

/**
 * Delete a session from the server (called on component unmount).
 * Fire-and-forget is fine — we don't block on it.
 *
 * @param {string} sessionId
 */
export async function clearChatSession(sessionId) {
  const response = await fetch(`${config.API_BASE_URL}/chat/${sessionId}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error("Failed to clear session");
  return response.json();
}

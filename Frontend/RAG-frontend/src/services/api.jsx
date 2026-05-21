import config from "../config/config";

// ─── Search ──────────────────────────────────────────────────────────────────

export async function searchPapers(queryData) {
  const response = await fetch(`${config.API_BASE_URL}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(queryData),
  });
  if (!response.ok) throw new Error("API request failed");
  return response.json();
}

export async function searchPapersWithProgress(queryData, onProgress) {
  const response = await fetch(`${config.API_BASE_URL}/search/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(queryData),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || "API request failed");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop();

    for (const chunk of chunks) {
      const trimmed = chunk.trim();
      if (!trimmed.startsWith("data:")) continue;

      const payload = trimmed.slice(5).trim();
      if (!payload) continue;

      const event = JSON.parse(payload);
      if (event.type === "progress") {
        onProgress?.(event.progress, event.total);
      } else if (event.type === "results") {
        return event.payload;
      } else if (event.type === "error") {
        throw new Error(event.message || "Search failed");
      }
    }
  }

  throw new Error("Stream ended without search results.");
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
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || "Chat request failed");
  }

  return response.json();
}

export async function startPaperChat({ entryId, pdfFile = null }) {
  const formData = new FormData();
  formData.append("entry_id", String(entryId));
  if (pdfFile) formData.append("pdf", pdfFile);

  const response = await fetch(`${config.API_BASE_URL}/paper/start`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || "Paper chat start failed");
  }

  return response.json();
}

export async function chatWithPaperSession({ sessionId, message, pdfFile = null }) {
  const formData = new FormData();
  formData.append("session_id", sessionId);
  formData.append("message", message);
  if (pdfFile) formData.append("pdf", pdfFile);

  const response = await fetch(`${config.API_BASE_URL}/paper/chat`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || "Paper chat request failed");
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

export async function clearPaperChatSession(sessionId) {
  const response = await fetch(`${config.API_BASE_URL}/paper/chat/${sessionId}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error("Failed to clear paper session");
  return response.json();
}

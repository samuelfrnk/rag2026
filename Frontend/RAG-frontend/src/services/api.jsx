import config from "../config/config";

// ─── Search ──────────────────────────────────────────────────────────────────

export async function searchPapers(queryData) {
  const response = await fetch(`${config.API_BASE_URL}/search`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(queryData),
  });
  if (!response.ok) throw new Error("API request failed");
  return response.json();
}

// ─── Global chat ──────────────────────────────────────────────────────────────

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

export async function clearChatSession(sessionId) {
  const response = await fetch(`${config.API_BASE_URL}/chat/${sessionId}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error("Failed to clear session");
  return response.json();
}

// ─── Individual paper chat ────────────────────────────────────────────────────

export async function paperStart(entryId) {
  const formData = new FormData();
  formData.append("entry_id", String(entryId));

  const response = await fetch(`${config.API_BASE_URL}/paper/start`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to start paper session");
  }

  return response.json();
}

export async function paperChat({ sessionId, message }) {
  const formData = new FormData();
  formData.append("session_id", sessionId);
  formData.append("message", message);

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

export async function clearPaperSession(sessionId) {
  const response = await fetch(`${config.API_BASE_URL}/paper/chat/${sessionId}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error("Failed to clear paper session");
  return response.json();
}

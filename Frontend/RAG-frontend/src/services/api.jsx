import config from "../config/config";

export async function pingBackend() {
  const response = await fetch(`${config.API_BASE_URL}/health`, {
    credentials: "include",
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export async function searchPapers(queryData) {
  const response = await fetch(`${config.API_BASE_URL}/search`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(queryData)
  });

  if (!response.ok) {
    throw new Error("API request failed");
  }

  return response.json();
}
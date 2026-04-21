// src/services/api.js
import config from "../config/config";

export async function searchPapers(data) {
  const formData = new FormData();

  formData.append("keywords", data.keywords);
  formData.append("text", data.text);
  formData.append("num_papers", data.numPapers);

  if (data.file) {
    formData.append("file", data.file);
  }

  const response = await fetch(`${config.API_BASE_URL}/search`, {
    method: "POST",
    body: formData
  });

  return response.json();
}
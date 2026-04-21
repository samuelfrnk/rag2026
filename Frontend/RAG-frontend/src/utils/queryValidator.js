import config from "../config/config";

export function validateQuery({ keywords, text, file, numPapers }) {
  const errors = [];

  // --- KEYWORDS ---
  if (keywords.length > config.MAX_KEYWORDS) {
    errors.push(`Max ${config.MAX_KEYWORDS} keywords allowed`);
  }

  // remove empty / trim
  const cleanedKeywords = keywords
    .map((k) => ({
      term: k.term.trim(),
      weight: Math.min(Math.max(k.weight, 1), 3) // clamp 1–3
    }))
    .filter((k) => k.term.length > 0);

    // --- TEST ERROR TRIGGER ---
    const hasTestErrorKeyword = cleanedKeywords.some(
        (k) => k.term.toLowerCase() === "test"
        );

        if (hasTestErrorKeyword) {
        errors.push("Test error triggered (keyword: 'test error')");
        }
  // remove duplicates
  const uniqueKeywords = Array.from(
    new Map(cleanedKeywords.map(k => [k.term, k])).values()
  );

  // --- TEXT ---
  const cleanedText = text.trim();

  if (cleanedText.length > 2000) {
    errors.push("Text too long (max 2000 chars)");
  }

  // --- FILE ---
  if (file) {
    const maxSizeMB = 5;
    if (file.size > maxSizeMB * 1024 * 1024) {
      errors.push("File too large (max 5MB)");
    }
  }

  // --- NUM PAPERS ---
  const safeNumPapers = Math.min(
    Math.max(numPapers, 1),
    config.MAX_PAPER_COUNT
  );

  return {
    isValid: errors.length === 0,
    errors,
    data: {
      keywords: uniqueKeywords,
      text: cleanedText,
      file,
      numPapers: safeNumPapers
    }
  };
}
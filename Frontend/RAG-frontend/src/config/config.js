const config = {
  API_BASE_URL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  DEFAULT_PAPER_COUNT: 4,
  MAX_PAPER_COUNT: 7,
  MIN_PAPER_COUNT: 1,
  MAX_KEYWORDS: 7
};

export default config;
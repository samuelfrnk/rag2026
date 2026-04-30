import { useState } from "react";
import Results from "./pages/Results";
import { Routes, Route, useNavigate } from "react-router-dom";
import Home from "./pages/Home";
import { searchPapers, pingBackend } from "./services/api";

function App() {
  const navigate = useNavigate();

  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [keywords, setKeywords] = useState([]);
  const [keywordInput, setKeywordInput] = useState("");
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [numPapers, setNumPapers] = useState(4);

  const canSubmit = keywords.length > 0;

  const [pingResult, setPingResult] = useState(null);
  const [pinging, setPinging] = useState(false);

  const handlePing = async () => {
    setPinging(true);
    setPingResult(null);
    try {
      const data = await pingBackend();
      setPingResult({ ok: true, message: JSON.stringify(data) });
    } catch (err) {
      setPingResult({ ok: false, message: err.message });
    } finally {
      setPinging(false);
    }
  };

  const handleSearch = async () => {
    setLoading(true);
    setError(null);

    try {
      const query = keywords.map((k) => k.term).join(" ");
      const data = await searchPapers({
        query: query + (text ? " " + text : ""),
        top_k: numPapers,
        sort_by: "relevance",
      });

      // Map API response shape → flat paper objects for Results page
      const mapped = (data.results || []).map((r) => ({
        title:    r.paper.title,
        authors:  r.paper.authors ? r.paper.authors.join(", ") : null,
        year:     r.paper.year,
        abstract: r.paper.abstract,
        score:    r.score,
        terms:    r.paper.terms,
        id:       r.paper.id,
      }));

      setPapers(mapped);
      navigate("/results");
    } catch (err) {
      setError("Failed to fetch papers. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ textAlign: "center", margin: "1rem 0" }}>
        <button onClick={handlePing} disabled={pinging}>
          {pinging ? "Pinging…" : "Ping Backend"}
        </button>
        {pingResult && (
          <p style={{ color: pingResult.ok ? "green" : "red", marginTop: "0.5rem" }}>
            {pingResult.ok ? "✓ " : "✗ "}{pingResult.message}
          </p>
        )}
      </div>

      <Routes>
        {/* HOME */}
        <Route
          path="/"
          element={
            <Home
              onSearch={handleSearch}
              keywords={keywords}
              setKeywords={setKeywords}
              keywordInput={keywordInput}
              setKeywordInput={setKeywordInput}
              text={text}
              setText={setText}
              file={file}
              setFile={setFile}
              numPapers={numPapers}
              setNumPapers={setNumPapers}
              canSubmit={canSubmit}
            />
          }
        />

        {/* RESULTS */}
        <Route
          path="/results"
          element={
            <Results papers={papers} loading={loading} error={error} />
          }
        />
      </Routes>
    </div>
  );
}

export default App;
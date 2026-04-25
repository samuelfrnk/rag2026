import { useState } from "react";
import Results from "./pages/Results";
import { Routes, Route, useNavigate } from "react-router-dom";
import Home from "./pages/Home";
import { searchPapers } from "./services/api";

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
      {/* <Header /> */}

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
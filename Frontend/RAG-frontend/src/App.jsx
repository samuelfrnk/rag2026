import { useState } from "react";
import Results from "./pages/Results";
import IndvPaper from "./pages/indv_paper";
import { Routes, Route, useNavigate } from "react-router-dom";
import Home from "./pages/Home";
import { searchPapersWithProgress } from "./services/api";

function App() {
  const navigate = useNavigate();

  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchProgress, setSearchProgress] = useState(0);

  const [keywords, setKeywords] = useState([]);
  const [keywordInput, setKeywordInput] = useState("");
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [numPapers, setNumPapers] = useState(4);

  const canSubmit = keywords.length > 0;

  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    setSearchProgress(0);
    navigate("/results");

    try {
      const query = keywords.map((k) => k.term).join(" ");
      const data = await searchPapersWithProgress(
        {
          query: query + (text ? " " + text : ""),
          top_k: numPapers,
          sort_by: "relevance",
        },
        (progress) => setSearchProgress(progress)
      );

      const mapped = (data.results || []).map((r) => ({
        title:      r.paper.title,
        authors:    r.paper.authors ? r.paper.authors.join(", ") : null,
        year:       r.paper.year,
        abstract:   r.paper.abstract,
        score:      r.score,
        categories: r.paper.terms,
        abs_url:    r.paper.abs_url,
        pdf_url:    r.paper.pdf_url,
        id:         r.paper.id,
      }));

      setPapers(mapped);
    } catch (err) {
      setError("Failed to fetch papers. Is the backend running?");
    } finally {
      setLoading(false);
      setSearchProgress(0);
    }
  };

  return (
    <div>
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
            <Results 
              papers={papers} 
              loading={loading} 
              error={error} 
              total={numPapers}
              progress={searchProgress}
              keywords={keywords}
              text={text}
              file={file}
              />
          }
        />
        <Route path="/indv_paper/:id" element={<IndvPaper keywords={keywords} text={text} file={file} />} />
      </Routes>
    </div>
  );
}

export default App;
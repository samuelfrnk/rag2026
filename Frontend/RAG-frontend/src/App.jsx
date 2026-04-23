import { useState } from "react";
import Results from "./pages/Results";
import { Routes, Route, useNavigate } from "react-router-dom";
import Home from "./pages/Home";

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
      const results = await new Promise((resolve) => {
        setTimeout(() => {
          resolve([
            {
              title: "Attention Is All You Need",
              authors: "Vaswani et al.",
              year: 2017,
              abstract: "We propose a new architecture..."
            }
          ]);
        }, 1000);
      });

      setPapers(results);
      navigate("/results");

    } catch (err) {
      setError("Failed to fetch papers.");
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
import { useState } from "react";
import Results from "./pages/Results";
import { Routes, Route, useNavigate } from "react-router-dom";
import Home from "./pages/Home";
import dummyPapers from "./data/dummyPapers";

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

    navigate("/results");

    try {
      await new Promise((resolve) => setTimeout(resolve, 4000));

      // simulate top-k selection
      const results = dummyPapers.slice(0, Math.min(numPapers, dummyPapers.length));
      console.log("numPapers:", numPapers);


      setPapers(results);

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
            <Results 
              papers={papers} 
              loading={loading} 
              error={error} 
              total={numPapers}
              keywords={keywords}
              text={text}
              file={file}
              />
          }
        />
      </Routes>
    </div>
  );
}

export default App;
import { useState } from "react";
import Header from "./components/Header/Header";
import SearchForm from "./components/SearchForm/SearchForm";
import Results from "./components/Results/Results";

function App() {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState(null);

  // 🔹 ALL form state moved here
  const [keywords, setKeywords] = useState([]);
  const [keywordInput, setKeywordInput] = useState("");
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [numPapers, setNumPapers] = useState(4);

  const canSubmit = keywords.length > 0;

  const handleSearch = async (query) => {
    setLoading(true);
    setHasSearched(true);
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
            },
            {
              title: "BERT: Pre-training of Deep Bidirectional Transformers",
              authors: "Devlin et al.",
              year: 2018,
              abstract: "We introduce BERT..."
            }
          ]);
        }, 1000);
      });

      setPapers(results);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch papers.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Header />

      <SearchForm
        // state
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

        // logic
        canSubmit={canSubmit}
        setError={setError}

        // submit
        onSearch={handleSearch}
      />

      {loading && <p style={{ textAlign: "center" }}>Searching...</p>}

      {error && <p style={{ color: "red", textAlign: "center" }}>{error}</p>}

      {!loading && hasSearched && !error && (
        <Results papers={papers} />
      )}
    </div>
  );
}

export default App;
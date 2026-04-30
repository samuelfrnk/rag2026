import { useState } from "react";
import Header from "../components/Header/Header";
import SearchForm from "../components/SearchForm/SearchForm";
import ModeToggle from "../components/ModeToggle/ModeToggle";
import { pingBackend } from "../services/api";

export default function Home(props) {
  const [mode, setMode] = useState("search"); // ✅ now inside component
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

  return (
    <>
      <Header />

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

      <ModeToggle mode={mode} setMode={setMode} />

      {mode === "search" && (
        <SearchForm
          onSearch={props.onSearch}
          keywords={props.keywords}
          setKeywords={props.setKeywords}
          keywordInput={props.keywordInput}
          setKeywordInput={props.setKeywordInput}
          text={props.text}
          setText={props.setText}
          file={props.file}
          setFile={props.setFile}
          numPapers={props.numPapers}
          setNumPapers={props.setNumPapers}
          canSubmit={props.canSubmit}
        />
      )}

      {mode === "qa" && (
        <div className="qa-placeholder">
          <h3>Ask about Papers</h3>
          <p>This feature is coming next.</p>
        </div>
      )}
    </>
  );
}
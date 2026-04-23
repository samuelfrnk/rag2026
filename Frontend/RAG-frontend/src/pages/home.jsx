import { useState } from "react";
import Header from "../components/Header/Header";
import SearchForm from "../components/SearchForm/SearchForm";
import ModeToggle from "../components/ModeToggle/ModeToggle";

export default function Home(props) {
  const [mode, setMode] = useState("search"); // ✅ now inside component

  return (
    <>
      <Header />

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
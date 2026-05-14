import { useState } from "react";
import Header from "../components/Header/Header";
import SearchForm from "../components/SearchForm/SearchForm";
import ModeToggle from "../components/ModeToggle/ModeToggle";
import PaperChatbot from "../components/Chatbot/Chatbot"; // ← adjust path to match your project structure
import "./home.css"

export default function Home(props) {
  const [mode, setMode] = useState("search");

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
        <div className="qa-container">
          {/* <p className="section-title">Ask our chatbot which will query our entire paper database!</p> */}
          {/* No `paper` prop → global RAG mode, searches all papers */}
          <PaperChatbot />
        </div>
      )}
    </>
  );
}

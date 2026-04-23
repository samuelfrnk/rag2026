import Slider from "../Slider/Slider";
import FileUpload from "../FileUpload/FileUpload";
import "./SearchForm.css";
import CustomDropdown from "../CustomDropdown/CustomDropdown";
import config from "../../config/config";

export default function SearchForm({
  onSearch,
  keywords,
  setKeywords,
  keywordInput,
  setKeywordInput,
  text,
  setText,
  file,
  setFile,
  numPapers,
  setNumPapers,
  canSubmit,
  errors,
  setErrors
}) {

  // ----------------------------
  // KEYWORD INPUT HANDLING
  // ----------------------------
  const handleKeywordKeyDown = (e) => {
    if (e.key !== "Enter") return;

    e.preventDefault();

    const value = keywordInput.trim();
    if (!value) return;

    if (keywords.length >= config.MAX_KEYWORDS) return;

    const exists = keywords.find((k) => k.term === value);
    if (exists) {
      setKeywordInput("");
      return;
    }

    setKeywords([
      ...keywords,
      { term: value, weight: 2 }
    ]);

    setKeywordInput("");
  };

  const removeKeyword = (term) => {
    setKeywords(keywords.filter((k) => k.term !== term));
  };

  const updateWeight = (term, newWeight) => {
    setKeywords(
      keywords.map((k) =>
        k.term === term ? { ...k, weight: newWeight } : k
      )
    );
  };

  // ----------------------------
  // SUBMIT (UI ONLY)
  // ----------------------------
  const handleSubmit = (e) => {
    e.preventDefault();

    if (!canSubmit) return;

  
    onSearch(); // App handles validation + processing + backend
  };

  return (
    <form onSubmit={handleSubmit} className="search-form">

      {/* ---------------- KEYWORD SECTION ---------------- */}
      <div className="keyword-section">

        <p className="keyword-label">
          Enter keywords to find relevant papers and optionally add weighting (1-3).
        </p>

        <p className="info">
          (3 = highly important and 1 = nice to have)
        </p>

        <div className="keyword-box">

          {errors?.length > 0 && (
            <div className="error-box">
              {errors.map((err, i) => (
                <p key={i} className="error-text">{err}</p>
              ))}
            </div>
          )}

          {/* INPUT ROW */}
          <div className="keyword-row input-row">
            <input
              className="keyword-input"
              type="text"
              placeholder={
                keywords.length >= config.MAX_KEYWORDS
                  ? "Max keywords reached"
                  : "Type keyword and press Enter"
              }
              value={keywordInput}
              onChange={(e) => setKeywordInput(e.target.value)}
              onKeyDown={handleKeywordKeyDown}
              disabled={keywords.length >= config.MAX_KEYWORDS}
            />
          </div>

          {/* CHIPS ROW */}
          <div className="keyword-row chips-row">
            {keywords.map((k) => (
              <div key={k.term} className="keyword-chip">

                <span className="keyword-text">{k.term}</span>

                <CustomDropdown
                  value={k.weight}
                  options={[1, 2, 3]}
                  onChange={(val) => updateWeight(k.term, val)}
                />

                <button
                  type="button"
                  onClick={() => removeKeyword(k.term)}
                >
                  ×
                </button>

              </div>
            ))}
          </div>

        </div>
      </div>

      {/* ---------------- LONG INPUT ---------------- */}
      <p className="keyword-label">
        Optional: add a description or upload a document.
      </p>

      <div className="long-input-row">

        <div className="text-column">
          <textarea
            placeholder="Paste your paragraph..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </div>

        <div className="file-column">
          <FileUpload onFileChange={setFile} />
        </div>

      </div>

      {/* ---------------- SLIDER ---------------- */}
      <Slider value={numPapers} onChange={setNumPapers} />

      {/* ---------------- SUBMIT ---------------- */}
      <button
        type="submit"
        className="submit-button"
        disabled={!canSubmit}
      >
        Retrieve papers
      </button>

    </form>
  );
}
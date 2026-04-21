// src/components/SearchForm/SearchForm.jsx
import { useState } from "react";
import Slider from "../Slider/Slider";
import FileUpload from "../FileUpload/FileUpload";
import "./SearchForm.css";
import CustomDropdown from "../CustomDropdown/CustomDropdown";
import config from "../../config/config";
import { validateQuery } from "../../utils/queryValidator";


export default function SearchForm({ onSearch }) {
  // keyword chips with weights
  const [keywords, setKeywords] = useState([]);
  const [keywordInput, setKeywordInput] = useState("");

  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [numPapers, setNumPapers] = useState(config.DEFAULT_PAPER_COUNT);
  const [errors, setErrors] = useState([]);
  // add keyword on Enter
  const handleKeywordKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();

      const value = keywordInput.trim();
      if (!value) return;

      // max keywords
      if (keywords.length >= config.MAX_KEYWORDS) {
        return;
      }

      // avoid duplicates
      const exists = keywords.find((k) => k.term === value);
      if (exists) {
        setKeywordInput("");
        return;
      }

      setKeywords([
        ...keywords,
        { term: value, weight: 2 } // default weight = 2
      ]);

      setKeywordInput("");
    }
  };

  // remove keyword
  const removeKeyword = (term) => {
    setKeywords(keywords.filter((k) => k.term !== term));
  };

  // update weight
  const updateWeight = (term, newWeight) => {
    setKeywords(
      keywords.map((k) =>
        k.term === term ? { ...k, weight: newWeight } : k
      )
    );
  };

  const handleSubmit = (e) => {
    console.log("SUBMIT TRIGGERED");
    e.preventDefault();

    const result = validateQuery({
      keywords,
      text,
      file,
      numPapers
    });

    if (!result.isValid) {
      setErrors(result.errors);
      return;
    }

    console.log("Validation result:", result);
    setErrors([]);
    onSearch(result.data);
  };

  return (
    <form onSubmit={handleSubmit} className="search-form">

      {/* KEYWORD SECTION */}
      <div className="keyword-section">

        <p className="keyword-label">
          Enter keywords to find relevant papers and optionally add weighting (1-5) to indicate importance.
        </p>

        <p className="info">
          (3 = highly important and 1 = nice to have)
        </p>

        {/* NEW WRAPPER */}
        <div className="keyword-box">
          
          {errors.length > 0 && (
            <div className="error-box">
              {errors.map((err, i) => (
                <p key={i} className="error-text">{err}</p>
              ))}
            </div>
          )}


          {/* ROW 1 */}
          <div className="keyword-row input-row">
            <input
              className="keyword-input"
              type="text"
              placeholder={
                keywords.length >= config.MAX_KEYWORDS
                  ? "Maximum only 7 keywords allowed!"
                  : "Type keyword and press Enter"
              }
              value={keywordInput}
              onChange={(e) => setKeywordInput(e.target.value)}
              onKeyDown={handleKeywordKeyDown}
              disabled={keywords.length >= config.MAX_KEYWORDS}

            />
          </div>

          {/* ROW 2 */}
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


      <p className="keyword-label">
        Optionally add a more detailed description/ paragraph of your work or even upload 1 pdf (max x pages)
      </p>

      <div className="long-input-row">

        {/* LEFT: TEXT AREA (2x width) */}
        <div className="text-column">
          <textarea
            placeholder="Paste your paragraph (max. x words)"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </div>

        {/* RIGHT: FILE UPLOAD (1x width) */}
        <div className="file-column">
          <FileUpload onFileChange={setFile} />
        </div>

      </div>

      








      {/* SLIDER */}
      <Slider value={numPapers} onChange={setNumPapers} />

      {/* SUBMIT */}
      <button type="submit" className="submit-button">
        Retrieve them papers!
      </button>
    </form>
  );
}
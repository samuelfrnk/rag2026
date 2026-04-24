import { useState } from "react";
import "./ResultCard.css";

export default function ResultCard({ paper, index }) {
  const [expanded, setExpanded] = useState(false); 

  const previewLength = 200;

  const preview =
    paper.abstract && paper.abstract.length > previewLength
      ? paper.abstract.slice(0, previewLength)
      : paper.abstract;

  return (
    <div className="result-card">

      {/* HEADER */}
      <div className="result-header">
        <div className="left">
          <span className="result-rank">#{index + 1}</span>
          <h3 className="result-title">{paper.title}</h3>
        </div>
        
        <div className="right">
          {/* SCORE */}
          {paper.score !== undefined && (
            <span className="result-score">
              {(paper.score * 100).toFixed(0)}% match
            </span>
          )}
        </div>
      </div>

      {/* METADATA */}
      <p className="result-meta">
        {paper.authors} • {paper.year} • {" "}
        <a
          href={`https://doi.org/${paper.doi}`}
          target="_blank"
          rel="noopener noreferrer"
          className="doi-link"
        >
          {paper.doi}
        </a>
      </p>

      {/* ABSTRACT */}
      <p className="result-abstract">
        {expanded ? paper.abstract : `${preview}...`}
      </p>

      {/* TOGGLE */}
      {paper.abstract && paper.abstract.length > previewLength && (
        <button
          className="expand-btn"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? "▲ Show less" : "▼ Show full abstract"}
        </button>
      )}
    </div>
  );
}
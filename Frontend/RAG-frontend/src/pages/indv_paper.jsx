import { useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { resolveCategories } from "../utils/categoryMap";
import "./IndvPaper.css";

export default function IndvPaper() {
  const [expandAbstract, setExpandAbstract] = useState(false);
  const location = useLocation();
  const params = useParams();
  const paperFromState = location.state?.paper;

  let paper = paperFromState;

  if (!paper) {
    const stored = localStorage.getItem("selectedPaper");
    if (stored) {
      try {
        paper = JSON.parse(stored);
      } catch (err) {
        paper = null;
      }
    }
  }

  if (!paper) {
    return (
       
      <div className="indv-page">
        <div className="indv-card">
          <h2>No paper selected</h2>
          <p>Please navigate from the results list to view a paper.</p>
          <Link to="/results" className="back-link">
            Back to results
          </Link>
        </div>
      </div>
    );
  }

  const resolvedCategories = resolveCategories(paper.categories);

  return (
    <div className="indv-page">
      <div className="indv-card">
        <div className="indv-header">

          <div className="top-row">
            <Link to="/results" className="back-link">
            ← Back to results
          </Link>
          <span className="indv-rank">Paper Rank: {params.id}</span>
          </div>

          <div className="bottom-row">
            <h1 className="indv-title">{paper.title}</h1>
          </div>
          
        </div>

        <p className="indv-meta">
          {paper.authors} • {paper.year} • {" "}
          <a
            href={`https://doi.org/${paper.doi}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            {paper.doi}
          </a>
        </p>

        <p className="indv-categories">
          Category tag(s): {resolvedCategories.length > 0 ? resolvedCategories.map((label) => (
            <span key={label} className="category-tag">
              {label}
            </span>
          )) : <span className="category-tag">Unknown Category</span>}
        </p>

        {paper.score !== undefined && (
          <p className="indv-score">Match score: {(paper.score * 100).toFixed(0)}%</p>
        )}

        <div className="indv-abstract">
          <h2>Abstract</h2>
          <div style={{ position: "relative" }}>
            <p>
              {expandAbstract 
                ? paper.abstract 
                : paper.abstract.length > 300 
                  ? paper.abstract.slice(0, 300) + "..." 
                  : paper.abstract
              }
            </p>
            {paper.abstract.length > 300 && (
              <button
                onClick={() => setExpandAbstract(!expandAbstract)}
                style={{
                  position: "absolute",
                  bottom: "0",
                  right: "0",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  fontSize: "1.2em",
                  padding: "0 5px"
                }}
              >
                {expandAbstract ? "▲" : "▼"}
              </button>
            )}
          </div>
        </div>

        <div className="chatbot-area">
          <h2>Chatbot</h2>
        <p>Ask anything about this paper!</p>
        </div>
      </div>
    </div>
  );
}

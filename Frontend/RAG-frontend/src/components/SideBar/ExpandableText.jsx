import { useState } from "react";

export default function ExpandableText({ text }) {
  const [expanded, setExpanded] = useState(false);

  const preview = text.slice(0, 120);

  return (
    <div className="sidebar-section">
      <p className="section-title">Description</p>

      <p className="expandable-text">
        {expanded ? text : `${preview}...`}
      </p>

      <button
        className="expand-btn"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? "Collapse Text ↑" : "Full Text ↓"}
      </button>
    </div>
  );
}
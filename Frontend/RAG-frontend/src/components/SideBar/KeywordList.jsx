export default function KeywordList({ keywords }) {
  if (!keywords?.length) return null;

  return (
    <div className="sidebar-section">
      <p className="section-title">Keywords (weight)</p>

      <div className="keyword-list">
        {keywords.map((k) => (
          <span key={k.term} className="keyword-chip-dark">
            {k.term} ({k.weight})
          </span>
        ))}
      </div>
    </div>
  );
}
import "./ProgressBar.css";

export default function ProgressBar({ total = 10, progress = 0 }) {
  const safeProgress = Math.min(Math.max(progress, 0), total);
  const percent = total > 0 ? (safeProgress / total) * 100 : 0;

  return (
    <div className="progress-wrapper">
      <div className="progress-title">
          Retrieving papers...
        </div>
      <div className="progress-bar">
        
        <div
          className="progress-fill"
          style={{ width: `${percent}%` }}
        />
      </div>

      <p className="progress-text">
        Retrieved {progress} / {total} papers
      </p>
    </div>
  );
}
import { useEffect, useState } from "react";
import "./ProgressBar.css";

export default function ProgressBar({ total = 10 }) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let current = 0;

    const interval = setInterval(() => {
      current += 1;
      setProgress(current);

      if (current >= total) {
        clearInterval(interval);
      }
    }, 10000 / total); // 10 seconds total

    return () => clearInterval(interval);
  }, [total]);

  const percent = (progress / total) * 100;

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
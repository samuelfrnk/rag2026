import "./Slider.css";
import config from "../../config/config";

export default function Slider({ value, onChange }) {
  const {
    MAX_PAPER_COUNT,
    DEFAULT_PAPER_COUNT,
    MIN_PAPER_COUNT
  } = config;

  const safeValue = Math.max(
    MIN_PAPER_COUNT,
    Math.min(value, MAX_PAPER_COUNT)
  );

  return (
    <div className="slider-wrapper">
      <label className="slider-label">
        Number of papers to retrieve (max: {MAX_PAPER_COUNT}):{" "}
      </label>

      <input
        type="range"
        min={MIN_PAPER_COUNT}
        max={MAX_PAPER_COUNT}
        value={safeValue}
        onChange={(e) => onChange(Number(e.target.value))}

        style={{
          background: `linear-gradient(
            to right,
            #5d3a8c 0%,
            #5d3a8c ${
              ((safeValue - MIN_PAPER_COUNT) /
                (MAX_PAPER_COUNT - MIN_PAPER_COUNT)) *
              100
            }%,
            #e5e5e5 ${
              ((safeValue - MIN_PAPER_COUNT) /
                (MAX_PAPER_COUNT - MIN_PAPER_COUNT)) *
              100
            }%,
            #e5e5e5 100%
          )`
        }}
      />

      <label className="slider-value">
        {safeValue}
      </label>
      
    </div>
  );
}
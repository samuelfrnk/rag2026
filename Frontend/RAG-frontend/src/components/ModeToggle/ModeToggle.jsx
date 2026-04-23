import "./ModeToggle.css";

export default function ModeToggle({ mode, setMode }) {
  return (
    <div className="mode-toggle">
      <button
        className={mode === "search" ? "active" : ""}
        onClick={() => setMode("search")}
      >
        Find Papers
      </button>

      <button
        className={mode === "qa" ? "active" : ""}
        onClick={() => setMode("qa")}
      >
        Ask about Papers
      </button>
    </div>
  );
}
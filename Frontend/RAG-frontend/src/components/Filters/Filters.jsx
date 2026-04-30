import { useState, useRef, useEffect } from "react";
import "./Filters.css";

function FilterDropdown({ value, options, onChange }) {
  const [open, setOpen] = useState(false);
  const ref = useRef();

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const selected = options.find((o) => o.value === value);

  return (
    <div className="filter-dropdown" ref={ref}>
      <div className="filter-dropdown-selected" onClick={() => setOpen(!open)}>
        {selected?.label || "-"}
        <span className="filter-arrow">▾</span>
      </div>

      {open && (
        <div className="filter-dropdown-menu">
          {options.map((opt) => (
            <div
              key={opt.value}
              className={`filter-dropdown-item ${opt.value === value ? "active" : ""}`}
              onClick={() => { onChange(opt.value); setOpen(false); }}
            >
              {opt.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Filters({ sortBy, setSortBy }) {
  const handleChange = (type, val) => {
    if (!val) return;
    setSortBy({ type, order: val });
  };

  return (
    <div className="filters">

      {/* YEAR FILTER */}
      <div className="filter-group">
        <label>Year</label>
        <FilterDropdown
          value={sortBy.type === "year" ? sortBy.order : null}
          options={[
            { value: "asc",  label: "Old → New" },
            { value: "desc", label: "New → Old" },
          ]}
          onChange={(val) => handleChange("year", val)}
        />
      </div>

      {/* SCORE FILTER */}
      <div className="filter-group">
        <label>Score</label>
        <FilterDropdown
          value={sortBy.type === "score" ? sortBy.order : null}
          options={[
            { value: "asc",  label: "Low → High" },
            { value: "desc", label: "High → Low" },
          ]}
          onChange={(val) => handleChange("score", val)}
        />
      </div>

    </div>
  );
}
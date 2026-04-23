// src/components/FileUpload/FileUpload.jsx
import { useRef, useState } from "react";
import "./FileUpload.css";

export default function FileUpload({ onFileChange }) {
  const inputRef = useRef(null);

  const [isDragging, setIsDragging] = useState(false);
  const [fileName, setFileName] = useState(null);
  const [error, setError] = useState(null);

  const allowedTypes = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
  ];

  const validateFile = (file) => {
    if (!file) return "No file selected";

    const isValidType = allowedTypes.includes(file.type);

    // fallback check (some browsers don't set DOCX type properly)
    const isValidExtension =
      file.name.endsWith(".pdf") || file.name.endsWith(".docx");

    if (!isValidType && !isValidExtension) {
      return "Only PDF and DOCX files are allowed";
    }

    return null;
  };

  const handleFile = (file) => {
    const validationError = validateFile(file);

    if (validationError) {
      setError(validationError);
      setFileName(null);
      onFileChange(null);
      return;
    }

    setError(null);
    setFileName(file.name);
    onFileChange(file);
  };

  // ---------------- DRAG EVENTS ----------------

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();

    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    handleFile(file);
  };

  // ---------------- UI ----------------

  return (
    <div className="file-upload-wrapper">
      <div
        className={`drop-zone ${isDragging ? "dragging" : ""}`}
        onDragOver={handleDragOver}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <p className="drop-title">Drag & drop your file here</p>

        <p className="drop-subtitle">PDF or DOCX only</p>

        <button
          type="button"
          className="upload-button"
          onClick={() => inputRef.current.click()}
        >
          Choose file
        </button>

        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          onChange={(e) => handleFile(e.target.files[0])}
          hidden
        />

        {fileName && (
          <p className="file-name">{fileName}</p>
        )}

        {error && (
          <p className="file-error">{error}</p>
        )}
      </div>
    </div>
  );
}
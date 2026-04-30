export default function FileInfo({ file }) {
  return (
    <div className="sidebar-section">
      <p className="section-title">Uploaded File</p>
      <p className="file-name-summary">{file.name}</p>
    </div>
  );
}
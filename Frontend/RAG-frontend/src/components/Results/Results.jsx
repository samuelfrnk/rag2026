import "./Results.css";

export default function Results({ papers }) {
  return (
    <div>
      <h2>Results</h2>
      {papers.map((p, i) => (
        <div key={i}>
          <h3>{p.title}</h3>
          <p>{p.authors} ({p.year})</p>
          <p>{p.abstract}</p>
        </div>
      ))}
    </div>
  );
}
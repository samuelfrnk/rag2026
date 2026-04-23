export default function Results({ papers, loading, error }) {
  if (loading) return <p>Loading...</p>;

  if (error) return <p style={{ color: "red" }}>{error}</p>;

  return (
    <div>
      <h2>Results</h2>

      {papers.map((paper, i) => (
        <div key={i}>
          <h3>{paper.title}</h3>
          <p>{paper.authors}</p>
          <p>{paper.year}</p>
          <p>{paper.abstract}</p>
        </div>
      ))}
    </div>
  );
}

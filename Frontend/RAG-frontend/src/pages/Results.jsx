import ProgressBar from "../components/ProgressBar/ProgressBar";
import Sidebar from "../components/Sidebar/Sidebar";
import "./Results.css";

export default function Results({ papers, loading, error, total, keywords, text, file }) {
  if (error) return <p style={{ color: "red" }}>{error}</p>;

  return (
    <div className="results-layout">

      {/* LEFT */}
      <Sidebar 
        inputs={{
          keywords,
          text,
          file
        }}
      />

      {/* RIGHT */}
      <div className="results-main">

        <h2 className="title">Top {total} Matches</h2>

        {loading && <ProgressBar total={total} />}

        {!loading &&
          papers.map((paper, i) => (
            <div key={i} className="paper-card">
              <h3>{paper.title}</h3>
              <p>{paper.authors}</p>
              <p>{paper.year}</p>
              <p>{paper.abstract}</p>
            </div>
          ))}

        {/* <Filters /> */}

        {/*<ResultsList papers={papers} loading={loading} error={error} />*/}
    
      </div>

    </div>
  );
}
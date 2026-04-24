import ProgressBar from "../components/ProgressBar/ProgressBar";
import Sidebar from "../components/Sidebar/Sidebar";
import ResultCard from "../components/Results/ResultCard";
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


        <div className="result-cards">
          {!loading &&
            papers.map((paper, i) => (
              <ResultCard key={paper.id || i} paper={paper} index={i} />
            ))}
        </div>

        {/* <Filters /> */}

        {/*<ResultsList papers={papers} loading={loading} error={error} />*/}
    
      </div>

    </div>
  );
}
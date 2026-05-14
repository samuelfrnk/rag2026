import ProgressBar from "../components/ProgressBar/ProgressBar";
import Sidebar from "../components/SideBar/SideBar";
import ResultCard from "../components/Results/ResultCard";
import "./Results.css";
import { useEffect, useState } from "react";
import Filters from "../components/Filters/Filters";

export default function Results({ papers, loading, error, total, keywords, text, file }) {
  if (error) return <p style={{ color: "red" }}>{error}</p>;
  
  const [sortBy, setSortBy] = useState({
    type: "score", // "score" | "year"
    order: "desc"  // "asc" | "desc"
  });

  const [visiblePapers, setVisiblePapers] = useState([]);

  useEffect(() => {
    if (loading) return;

    if (papers.length === 0) {
      setVisiblePapers([]);
      return;
    }

    setVisiblePapers([]);
    const timers = papers.map((paper, index) =>
      setTimeout(() => {
        setVisiblePapers((prev) => [...prev, paper]);
      }, index * 500)
    );

    return () => timers.forEach(clearTimeout);
  }, [loading, papers]);

  const sortedPapers = [...visiblePapers].sort((a, b) => {
    if (sortBy.type === "score") {
      return sortBy.order === "desc" ? b.score - a.score : a.score - b.score;
    }

    if (sortBy.type === "year") {
      return sortBy.order === "desc" ? b.year - a.year : a.year - b.year;
    }

    return 0;
  });

  if (loading) {
    return (
      <div className="results-layout">
        <Sidebar
          inputs={{
            keywords,
            text,
            file
          }}
        />

        <div className="results-main">
          <div className="results-loading">
            <ProgressBar total={total} />
          </div>
        </div>
      </div>
    );
  }

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

        <h2 className="title">Yo Top {total} Matches</h2>

        <div className="disclaimer">
          <p className="disclaimer-text">
            The score is based on cosine similarity. <br />
            Please review the papers for relevance by simply clicking on it.
          </p>
        </div>

        {/* <Filters /> */}
        <Filters sortBy={sortBy} setSortBy={setSortBy} />
        <div className="divider" />


        {/*<ResultsList papers={papers} loading={loading} error={error} />*/}
        <div className="result-cards">
          {!loading &&
            sortedPapers.map((paper, i) => (
              <ResultCard key={paper.id || i} paper={paper} index={i} />
            ))}
        </div>

        

    
      </div>

    </div>
  );
}
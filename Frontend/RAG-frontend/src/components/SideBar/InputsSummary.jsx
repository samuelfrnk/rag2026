import KeywordList from "./KeywordList";
import ExpandableText from "./ExpandableText";
import FileInfo from "./FileInfo";

export default function InputsSummary({ inputs }) {
  const { keywords, text, file } = inputs;

  return (
    <div className="inputs-summary">

      <h3 className="section-title">Your Inputs</h3>

      <KeywordList keywords={keywords} />

      {text && <ExpandableText text={text} />}

      {file && <FileInfo file={file} />}

    </div>
  );
}
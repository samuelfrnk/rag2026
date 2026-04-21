import Header from "../components/Header/Header";
import SearchForm from "../components/SearchForm/SearchForm";
import { searchPapers } from "../services/api";

export default function Home() {
  const handleSearch = async (data) => {
    const results = await searchPapers(data);
    console.log(results);
  };

  return (
    <>
      <Header />
      <SearchForm onSearch={handleSearch} />
    </>
  );
}
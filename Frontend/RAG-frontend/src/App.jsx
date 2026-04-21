import Header from "./components/Header/Header";
import SearchForm from "./components/SearchForm/SearchForm";

function App() {
  const handleSearch = (data) => {
    console.log("Search data:", data);
    // later → call backend here
  };

  return (
    <>
      <Header />
      <SearchForm onSearch={handleSearch} />
    </>
  );
}

export default App;
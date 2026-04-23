// src/components/Header/Header.jsx
import "./Header.css";
import logo from "/logo_test1.png";

export default function Header() {
  return (
    <header className="header">

      <img src={logo} alt="logo" className="logo" />
      <h1>YoPaLM</h1>
    
      <p className="slogan">Your Paper Language Model</p>
    </header>
  );
}
import { useNavigate } from "react-router-dom";
import logo from "/logo_v2.png";

export default function SidebarHeader({ onBack }) {
  const navigate = useNavigate();

  const handleBack = () => {
    if (onBack) onBack();
    else navigate("/");
  };

  return (
    <div className="sidebar-header">

      <div className="sidebar-logo">
        <img src={logo} alt="logo" />
        <span>YoPaLM</span>
      </div>

      <button className="back-button" onClick={handleBack}>
        ← Back
      </button>

    </div>
  );
}
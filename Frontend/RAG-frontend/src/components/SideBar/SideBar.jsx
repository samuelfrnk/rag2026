import "./SideBar.css";
import SidebarHeader from "./SidebarHeader";
import InputsSummary from "./InputsSummary";

export default function Sidebar({ inputs, onBack }) {
  return (
    <div className="sidebar">

      <SidebarHeader onBack={onBack} />

      <InputsSummary inputs={inputs} />

    </div>
  );
}
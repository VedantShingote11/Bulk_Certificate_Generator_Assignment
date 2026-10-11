import { NavLink } from "react-router-dom";
import { LayoutDashboard, FilePlus, List, Award, Layers } from "lucide-react";

const NAV = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/create", icon: FilePlus, label: "New Job" },
  { to: "/jobs", icon: List, label: "All Jobs" },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-mark">
          <Layers size={18} color="#fff" />
        </div>
        <div className="logo-title">CertForge</div>
        <div className="logo-subtitle">Certificate Generator</div>
      </div>

      <div className="nav-section">
        <div className="nav-label">Navigation</div>
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
          >
            <Icon className="nav-icon" size={16} />
            {label}
          </NavLink>
        ))}
      </div>

      <div className="sidebar-footer">
        <div style={{
          display: "flex", alignItems: "center", gap: 8,
          padding: "8px 10px",
          background: "var(--bg-subtle)",
          borderRadius: "var(--radius-sm)",
          border: "1px solid var(--border)",
        }}>
          <Award size={14} color="var(--blue)" />
          <span style={{ fontSize: 11, color: "var(--text-muted)", lineHeight: 1.4 }}>
            PDF certificates · A4 landscape
          </span>
        </div>
      </div>
    </aside>
  );
}

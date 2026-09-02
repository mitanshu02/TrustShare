import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/useAuth";
import "./DashboardLayout.css";

const NAV_ITEMS = [
  { to: "/dashboard", label: "My Files", end: true, icon: FolderIcon },
  { to: "/dashboard/shared", label: "Shared with Me", icon: ShareIcon },
  { to: "/dashboard/activity", label: "Activity", icon: ActivityIcon },
  { to: "/dashboard/stats", label: "Statistics", icon: StatsIcon },
];

function FolderIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none">
      <path
        d="M3 6a1 1 0 0 1 1-1h5l2 2h9a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ShareIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none">
      <circle cx="6" cy="12" r="2.5" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="18" cy="6" r="2.5" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="18" cy="18" r="2.5" stroke="currentColor" strokeWidth="1.6" />
      <path d="M8.2 10.8 15.8 7.2M8.2 13.2l7.6 3.6" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}

function ActivityIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none">
      <path
        d="M3 12h4l2-7 4 14 2-7h6"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function StatsIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none">
      <path
        d="M4 20V10M12 20V4M20 20v-7"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  );
}

export default function DashboardLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="dash-layout">
      <aside className="dash-sidebar">
        <div className="dash-sidebar__mark">TrustShare</div>
        <nav className="dash-sidebar__nav">
          {NAV_ITEMS.map(({ to, label, end, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                "dash-sidebar__link" + (isActive ? " active" : "")
              }
            >
              <Icon />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="dash-body">
        <header className="dash-topbar">
          <span className="dash-topbar__user">
            {user?.full_name} · {user?.email}
          </span>
          <button className="dash-topbar__logout" onClick={logout}>
            Log out
          </button>
        </header>

        <main className="dash-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
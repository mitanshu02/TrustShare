import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";
import { getUnreadNotificationCount } from "../api/monitoring";
import "./DashboardLayout.css";

const UNREAD_POLL_MS = 30000;

const NAV_ITEMS = [
  { to: "/dashboard", label: "My Files", end: true, icon: FolderIcon },
  { to: "/dashboard/shared", label: "Shared with Me", icon: ShareIcon },
  { to: "/dashboard/activity", label: "Activity", icon: ActivityIcon },
  { to: "/dashboard/notifications", label: "Notifications", icon: NotificationIcon },
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
      <path
        d="M8.2 10.8 15.8 7.2M8.2 13.2l7.6 3.6"
        stroke="currentColor"
        strokeWidth="1.6"
      />
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

function NotificationIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none">
      <path
        d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M10 21h4"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
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

function AdminIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none">
      <path
        d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function DashboardLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);

  const navItems =
    user?.role === "admin"
      ? [...NAV_ITEMS, { to: "/dashboard/admin", label: "Admin", icon: AdminIcon }]
      : NAV_ITEMS;

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const count = await getUnreadNotificationCount();
        if (!cancelled) setUnreadCount(count);
      } catch {
        // Silently skip a failed poll — the badge just won't update
        // this cycle, and will try again on the next interval.
      }
    }

    poll();
    const intervalId = setInterval(poll, UNREAD_POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, []);

  return (
    <div className="dash-layout">
      <aside className="dash-sidebar">
        <div className="dash-sidebar__mark">TrustShare</div>

        <nav className="dash-sidebar__nav">
          {navItems.map(({ to, label, end, icon: Icon }) => (
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
              {to === "/dashboard/notifications" && unreadCount > 0 && (
                <span
                  style={{
                    marginLeft: "auto",
                    background: "var(--gold)",
                    color: "var(--bg, #1a1a1a)",
                    borderRadius: "999px",
                    fontSize: "0.7rem",
                    fontWeight: 700,
                    padding: "0.05rem 0.45rem",
                    minWidth: "1.2rem",
                    textAlign: "center",
                  }}
                >
                  {unreadCount > 99 ? "99+" : unreadCount}
                </span>
              )}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="dash-body">
        <header className="dash-topbar">
          <span className="dash-topbar__user">
            {user?.full_name} · {user?.email}
          </span>

          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <button
              type="button"
              onClick={() => navigate("/dashboard/notifications")}
              aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ""}`}
              style={{
                position: "relative",
                background: "transparent",
                border: "none",
                cursor: "pointer",
                color: "var(--text)",
                width: "28px",
                height: "28px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <NotificationIcon />
              {unreadCount > 0 && (
                <span
                  style={{
                    position: "absolute",
                    top: "-2px",
                    right: "-2px",
                    background: "#e35555",
                    color: "#fff",
                    borderRadius: "999px",
                    fontSize: "0.62rem",
                    fontWeight: 700,
                    lineHeight: 1,
                    padding: "0.18rem 0.35rem",
                    minWidth: "1rem",
                  }}
                >
                  {unreadCount > 99 ? "99+" : unreadCount}
                </span>
              )}
            </button>

            <button className="dash-topbar__logout" onClick={logout}>
              Log out
            </button>
          </div>
        </header>

        <main className="dash-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
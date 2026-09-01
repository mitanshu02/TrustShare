import { useAuth } from "../context/useAuth";
import "./Dashboard.css";

export default function Dashboard() {
  const { user, logout } = useAuth();

  return (
    <div className="dashboard">
      <nav className="dashboard__nav">
        <span className="dashboard__mark">TrustShare</span>
        <div className="dashboard__user">
          <span className="dashboard__user-name">
            {user?.full_name} · {user?.email}
          </span>
          <button className="dashboard__logout" onClick={logout}>
            Log out
          </button>
        </div>
      </nav>

      <main className="dashboard__main">
        <svg
          className="dashboard__empty-icon"
          viewBox="0 0 64 64"
          fill="none"
        >
          <rect
            x="14"
            y="28"
            width="36"
            height="28"
            rx="4"
            stroke="currentColor"
            strokeWidth="2.5"
          />
          <path
            d="M22 28V20a10 10 0 0 1 20 0v8"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            fill="none"
          />
        </svg>
        <h1>Nothing here yet</h1>
        <p>
          Loading....
        </p>
        <button className="dashboard__upload-btn" disabled>
          Upload a file
        </button>
      </main>
    </div>
  );
}
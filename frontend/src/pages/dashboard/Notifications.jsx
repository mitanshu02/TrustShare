import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "../../api/monitoring";

const TYPE_LABELS = {
  new_login: "Login",
  file_shared: "Shared",
  file_downloaded: "Download",
  security_alert: "Security",
  link_expiring_soon: "Expiring link",
  key_rotated: "Key rotation",
};

export default function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    getNotifications()
      .then(setNotifications)
      .catch(() => setError("Unable to load notifications."))
      .finally(() => setLoading(false));
  }, []);

  const unreadCount = notifications.filter((item) => !item.read_at).length;

  async function markRead(id) {
    try {
      await markNotificationRead(id);
      setNotifications((items) =>
        items.map((item) =>
          item.id === id
            ? { ...item, read_at: new Date().toISOString() }
            : item
        )
      );
    } catch {
      setError("Unable to update notification.");
    }
  }

  async function markAllRead() {
    try {
      await markAllNotificationsRead();
      const now = new Date().toISOString();
      setNotifications((items) =>
        items.map((item) => (item.read_at ? item : { ...item, read_at: now }))
      );
    } catch {
      setError("Unable to update notifications.");
    }
  }

  function handleOpen(item) {
    if (!item.read_at) markRead(item.id);
    if (item.link_url) navigate(item.link_url);
  }

  return (
    <div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "1.5rem",
        }}
      >
        <h1 style={{ fontSize: "1.3rem", margin: 0 }}>
          Notifications
          {unreadCount > 0 && (
            <span
              style={{
                marginLeft: "0.6rem",
                fontSize: "0.8rem",
                fontWeight: 500,
                color: "var(--text-muted)",
              }}
            >
              ({unreadCount} unread)
            </span>
          )}
        </h1>

        {unreadCount > 0 && (
          <button
            type="button"
            onClick={markAllRead}
            style={{
              background: "transparent",
              border: "1px solid var(--border)",
              color: "var(--text)",
              borderRadius: "8px",
              padding: "0.45rem 1rem",
              fontSize: "0.85rem",
              cursor: "pointer",
            }}
          >
            Mark all as read
          </button>
        )}
      </div>

      {error && <p>{error}</p>}
      {loading && <p>Loading…</p>}

      {!loading && notifications.length === 0 && <p>No notifications yet.</p>}

      {notifications.map((item) => (
        <article
          key={item.id}
          onClick={() => handleOpen(item)}
          style={{
            marginBottom: "12px",
            padding: "16px",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            opacity: item.read_at ? 0.65 : 1,
            cursor: item.link_url ? "pointer" : "default",
            position: "relative",
          }}
        >
          <span
            style={{
              display: "inline-block",
              fontSize: "0.7rem",
              textTransform: "uppercase",
              letterSpacing: "0.04em",
              color: "var(--gold)",
              marginBottom: "0.3rem",
            }}
          >
            {TYPE_LABELS[item.notification_type] || item.notification_type}
          </span>

          {!item.read_at && (
            <span
              title="Unread"
              style={{
                position: "absolute",
                top: "18px",
                right: "16px",
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                background: "var(--gold)",
              }}
            />
          )}

          <h3 style={{ margin: "0 0 0.3rem" }}>{item.title}</h3>
          <p style={{ margin: "0 0 0.4rem" }}>{item.message}</p>
          <small style={{ color: "var(--text-muted)" }}>
            {new Date(item.created_at).toLocaleString()}
          </small>

          {!item.read_at && (
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                markRead(item.id);
              }}
              style={{
                display: "block",
                marginTop: "0.6rem",
                background: "transparent",
                border: "1px solid var(--border)",
                color: "var(--text)",
                borderRadius: "6px",
                padding: "0.3rem 0.8rem",
                fontSize: "0.78rem",
                cursor: "pointer",
              }}
            >
              Mark as read
            </button>
          )}
        </article>
      ))}
    </div>
  );
}

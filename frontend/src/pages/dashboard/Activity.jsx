import { useEffect, useState } from "react";
import { getActivity } from "../../api/files";
import { exportAuditLog, getAuditLog, getSecurityStatus } from "../../api/auditLog";
import "./Activity.css";

function describeEvent(event) {
  switch (event.type) {
    case "upload":
      return { text: `You uploaded ${event.file_name}`, tone: "neutral" };
    case "download":
      return event.counterpart_email === "you"
        ? { text: `You downloaded ${event.file_name}`, tone: "neutral" }
        : {
            text: `${event.counterpart_email} downloaded ${event.file_name}`,
            tone: "teal",
          };
    case "share_out":
      return {
        text: `You shared ${event.file_name} with ${event.counterpart_email} (${event.access_level})`,
        tone: "gold",
      };
    case "share_in":
      return {
        text: `${event.counterpart_email} shared ${event.file_name} with you (${event.access_level})`,
        tone: "gold",
      };
    default:
      return { text: event.file_name, tone: "neutral" };
  }
}

function timeAgo(isoString) {
  const diffMs = Date.now() - new Date(isoString).getTime();
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

const EVENT_TYPE_OPTIONS = [
  { value: "", label: "All actions" },
  { value: "login_success", label: "Login" },
  { value: "login_failed", label: "Failed login" },
  { value: "suspicious_login_activity", label: "Suspicious activity" },
  { value: "file_uploaded", label: "Upload" },
  { value: "file_downloaded", label: "Download" },
  { value: "file_deleted", label: "Delete" },
  { value: "file_key_rotated", label: "Key rotation" },
  { value: "file_shared", label: "Share" },
  { value: "share_link_created", label: "Link created" },
  { value: "share_link_revoked", label: "Link revoked" },
  { value: "public_link_downloaded", label: "Link download" },
];

const CATEGORY_TABS = [
  { value: "all", label: "All" },
  { value: "uploads", label: "Uploads" },
  { value: "downloads", label: "Downloads" },
  { value: "shares", label: "Shares" },
  { value: "security", label: "Security" },
];

function SecurityStatusCard() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    let cancelled = false;
    getSecurityStatus()
      .then((data) => {
        if (!cancelled) setStatus(data);
      })
      .catch(() => {
        // Non-critical widget — fail quietly rather than blocking the page.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!status) return null;

  const isSuspicious = status.suspicious_activity;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.9rem",
        padding: "0.9rem 1.1rem",
        borderRadius: "10px",
        border: `1px solid ${isSuspicious ? "var(--danger)" : "var(--border)"}`,
        background: isSuspicious ? "var(--danger-soft)" : "var(--surface)",
        marginBottom: "1.5rem",
      }}
    >
      <span
        style={{
          width: "10px",
          height: "10px",
          borderRadius: "50%",
          background: isSuspicious ? "var(--danger)" : "var(--teal)",
          flexShrink: 0,
        }}
      />
      <div>
        <strong style={{ fontSize: "0.9rem" }}>
          {isSuspicious ? "Suspicious activity detected" : "No suspicious activity detected"}
        </strong>
        <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
          {status.failed_logins_15m} failed login attempt(s) in the last 15 minutes
          {isSuspicious && status.reason ? ` · ${status.reason}` : ""}
        </div>
      </div>
    </div>
  );
}

function AuditLogSection() {
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [category, setCategory] = useState("all");
  const [q, setQ] = useState("");
  const [eventType, setEventType] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load(activeCategory = category) {
    setLoading(true);
    setError("");
    try {
      const data = await getAuditLog({
        category: activeCategory !== "all" ? activeCategory : undefined,
        q: q || undefined,
        eventType: eventType || undefined,
        dateFrom: dateFrom ? new Date(dateFrom).toISOString() : undefined,
        dateTo: dateTo ? new Date(dateTo).toISOString() : undefined,
        limit: 100,
      });
      setRows(data.events);
      setTotal(data.total);
    } catch {
      setError("Couldn't load the audit log.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleTabClick(value) {
    setCategory(value);
    load(value);
  }

  function handleSearch(e) {
    e.preventDefault();
    load();
  }

  async function handleExport() {
    try {
      await exportAuditLog({
        category: category !== "all" ? category : undefined,
        q: q || undefined,
        eventType: eventType || undefined,
        dateFrom: dateFrom ? new Date(dateFrom).toISOString() : undefined,
        dateTo: dateTo ? new Date(dateTo).toISOString() : undefined,
      });
    } catch {
      setError("Couldn't export the audit log.");
    }
  }

  return (
    <div style={{ marginTop: "2.5rem" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "1rem",
        }}
      >
        <h2 style={{ fontSize: "1.1rem", margin: 0 }}>
          Audit log{total > 0 && (
            <span style={{ fontWeight: 400, fontSize: "0.85rem", color: "var(--text-muted)" }}>
              {" "}
              ({total} events)
            </span>
          )}
        </h2>

        <button
          type="button"
          onClick={handleExport}
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
          Export CSV
        </button>
      </div>

      <div style={{ display: "flex", gap: "0.4rem", marginBottom: "1rem" }}>
        {CATEGORY_TABS.map((tab) => (
          <button
            key={tab.value}
            type="button"
            onClick={() => handleTabClick(tab.value)}
            style={{
              background: category === tab.value ? "var(--gold)" : "transparent",
              color: category === tab.value ? "var(--on-gold)" : "var(--text)",
              border: "1px solid var(--border)",
              borderRadius: "999px",
              padding: "0.35rem 0.9rem",
              fontSize: "0.8rem",
              fontWeight: category === tab.value ? 600 : 400,
              cursor: "pointer",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <form
        onSubmit={handleSearch}
        style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem", marginBottom: "1.2rem" }}
      >
        <input
          type="text"
          placeholder="Search activity description…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          style={{
            flex: "1 1 220px",
            padding: "0.5rem 0.7rem",
            borderRadius: "8px",
            border: "1px solid var(--border)",
            background: "var(--surface)",
            color: "var(--text)",
          }}
        />

        <select
          value={eventType}
          onChange={(e) => setEventType(e.target.value)}
          style={{
            padding: "0.5rem 0.7rem",
            borderRadius: "8px",
            border: "1px solid var(--border)",
            background: "var(--surface)",
            color: "var(--text)",
          }}
        >
          {EVENT_TYPE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        <input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          style={{
            padding: "0.5rem 0.7rem",
            borderRadius: "8px",
            border: "1px solid var(--border)",
            background: "var(--surface)",
            color: "var(--text)",
          }}
        />
        <input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          style={{
            padding: "0.5rem 0.7rem",
            borderRadius: "8px",
            border: "1px solid var(--border)",
            background: "var(--surface)",
            color: "var(--text)",
          }}
        />

        <button
          type="submit"
          style={{
            background: "var(--gold)",
            border: "none",
            color: "var(--on-gold)",
            fontWeight: 600,
            borderRadius: "8px",
            padding: "0.5rem 1.1rem",
            cursor: "pointer",
          }}
        >
          Search
        </button>
      </form>

      {error && <div className="myfiles__error">{error}</div>}
      {loading && <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Loading…</p>}

      {!loading && rows.length === 0 && (
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>No matching events.</p>
      )}

      {!loading && rows.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          {rows.map((row) => (
            <div
              key={row.id}
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: "1rem",
                padding: "0.7rem 0.9rem",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                fontSize: "0.85rem",
              }}
            >
              <div>
                <strong>{row.event_type.replaceAll("_", " ")}</strong>
                {row.file_name && <span> · {row.file_name}</span>}
                {row.actor_email && (
                  <span style={{ color: "var(--text-muted)" }}> · {row.actor_email}</span>
                )}
              </div>
              <span style={{ color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                {new Date(row.created_at).toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Activity() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await getActivity();
        if (!cancelled) setEvents(data);
      } catch {
        if (!cancelled) setError("Couldn't load activity.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <h1 style={{ fontSize: "1.3rem", marginBottom: "1.5rem" }}>Activity</h1>

      <SecurityStatusCard />

      {error && <div className="myfiles__error">{error}</div>}

      {loading ? (
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Loading…</p>
      ) : events.length === 0 ? (
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
          No activity yet — uploads, downloads, and shares will show up here.
        </p>
      ) : (
        <ul className="activity__list">
          {events.map((event, i) => {
            const { text, tone } = describeEvent(event);
            return (
              <li key={i} className="activity__item">
                <span className={`activity__dot activity__dot--${tone}`} />
                <span className="activity__text">{text}</span>
                <span className="activity__time">{timeAgo(event.timestamp)}</span>
              </li>
            );
          })}
        </ul>
      )}

      <AuditLogSection />
    </div>
  );
}

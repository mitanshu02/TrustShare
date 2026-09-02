import { useEffect, useState } from "react";
import { getActivity } from "../../api/files";
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
    </div>
  );
}
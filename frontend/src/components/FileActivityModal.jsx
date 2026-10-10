import { useEffect, useState } from "react";
import { getFileActivityReport } from "../api/files";
import "./ShareModal.css";

const EVENT_LABELS = {
  file_uploaded: "Uploaded",
  file_downloaded: "Downloaded",
  file_deleted: "Deleted",
  file_key_rotated: "Encryption key rotated",
  file_shared: "Shared",
  file_permission_updated: "Sharing permission updated",
  file_permission_revoked: "Sharing permission revoked",
  share_link_created: "Share link created",
  share_link_revoked: "Share link revoked",
  public_link_downloaded: "Downloaded via share link",
  public_link_viewed: "Viewed via share link",
};

function describe(event) {
  return EVENT_LABELS[event.event_type] || event.event_type.replaceAll("_", " ");
}

export default function FileActivityModal({ file, onClose }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await getFileActivityReport(file.id);
        if (!cancelled) setReport(data);
      } catch {
        if (!cancelled) setError("Couldn't load this file's activity.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [file.id]);

  const activity = report?.events || [];

  return (
    <div className="share-modal__backdrop" onClick={onClose}>
      <div className="share-modal" onClick={(e) => e.stopPropagation()}>
        <div className="share-modal__header">
          <h3>Activity for "{file.original_name}"</h3>
          <button className="share-modal__close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        {error && <div className="share-modal__error">{error}</div>}
        {loading && <p className="share-modal__muted">Loading…</p>}

        {report && (
          <div
            style={{
              display: "flex",
              gap: "1.5rem",
              marginBottom: "1rem",
              paddingBottom: "0.9rem",
              borderBottom: "1px solid var(--border)",
            }}
          >
            <div>
              <strong style={{ fontSize: "1.1rem" }}>{report.total_events}</strong>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Total events</div>
            </div>
            <div>
              <strong style={{ fontSize: "1.1rem" }}>{report.downloads}</strong>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Downloads</div>
            </div>
            <div>
              <strong style={{ fontSize: "1.1rem" }}>{report.temporary_links}</strong>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Temporary links</div>
            </div>
          </div>
        )}

        {!loading && activity.length === 0 && (
          <p className="share-modal__muted">No recorded activity for this file yet.</p>
        )}

        {!loading && activity.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {activity.map((event) => (
              <div
                key={event.id}
                style={{
                  borderLeft: "2px solid var(--border)",
                  paddingLeft: "0.9rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: "0.5rem" }}>
                  <strong style={{ fontSize: "0.88rem" }}>{describe(event)}</strong>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    {new Date(event.created_at).toLocaleString()}
                  </span>
                </div>
                <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                  {event.actor_email || "System / public link"}
                  {event.ip_address ? ` · ${event.ip_address}` : ""}
                  {event.severity !== "info" ? ` · ${event.severity}` : ""}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

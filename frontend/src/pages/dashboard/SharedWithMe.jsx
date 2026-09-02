import { useEffect, useState } from "react";
import { downloadFile, listSharedWithMe } from "../../api/files";
import "./MyFiles.css";

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(1)} ${units[unitIndex]}`;
}

export default function SharedWithMe() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await listSharedWithMe();
        if (!cancelled) setFiles(data);
      } catch {
        if (!cancelled) setError("Couldn't load files shared with you.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleDownload(file) {
    try {
      await downloadFile(file.id, file.original_name);
    } catch {
      setError("Couldn't download that file.");
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: "1.3rem", marginBottom: "1.5rem" }}>Shared with me</h1>

      {error && <div className="myfiles__error">{error}</div>}

      {loading ? (
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Loading…</p>
      ) : files.length === 0 ? (
        <div className="myfiles__empty">
          <svg className="myfiles__empty-icon" viewBox="0 0 24 24" fill="none">
            <circle cx="6" cy="12" r="2.5" stroke="currentColor" strokeWidth="1.6" />
            <circle cx="18" cy="6" r="2.5" stroke="currentColor" strokeWidth="1.6" />
            <circle cx="18" cy="18" r="2.5" stroke="currentColor" strokeWidth="1.6" />
            <path d="M8.2 10.8 15.8 7.2M8.2 13.2l7.6 3.6" stroke="currentColor" strokeWidth="1.6" />
          </svg>
          <h2>Nothing shared with you yet</h2>
          <p>When someone shares a file with your email, it'll show up here.</p>
        </div>
      ) : (
        <div className="myfiles__list">
          {files.map((file) => (
            <div key={file.id} className="myfiles__item">
              <svg className="myfiles__item-icon myfiles__item-icon--file" viewBox="0 0 24 24" fill="none">
                <path d="M6 3h8l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
                <path d="M14 3v5h5" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
              </svg>
              <span className="myfiles__item-name">{file.original_name}</span>
              <span className="myfiles__item-meta">
                {formatBytes(file.size_bytes)} · from {file.shared_by_email} ·{" "}
                {file.access_level === "download" ? "can download" : "view only"}
              </span>
              {file.access_level === "download" && (
                <div className="myfiles__item-actions">
                  <button
                    className="myfiles__icon-btn"
                    title="Download"
                    onClick={() => handleDownload(file)}
                  >
                    <svg viewBox="0 0 24 24" fill="none">
                      <path d="M12 4v11m0 0-4-4m4 4 4-4M5 19h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
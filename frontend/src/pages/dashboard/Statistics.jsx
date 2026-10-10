import { useEffect, useState } from "react";
import { getStats, getStorageStats } from "../../api/files";
import "./Statistics.css";

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

const TYPE_LABELS = {
  images: "Images",
  pdf: "PDFs",
  documents: "Documents",
  video: "Video",
  other: "Other",
};

export default function Statistics() {
  const [stats, setStats] = useState(null);
  const [storageStats, setStorageStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [overview, byType] = await Promise.all([
          getStats(),
          getStorageStats(),
        ]);
        if (!cancelled) {
          setStats(overview);
          setStorageStats(byType);
        }
      } catch {
        if (!cancelled) setError("Couldn't load statistics.");
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const cards = stats
    ? [
        { label: "Files stored", value: stats.file_count },
        { label: "Storage used", value: formatBytes(stats.total_storage_bytes) },
        { label: "Files you've shared", value: stats.files_shared_out },
        { label: "Files shared with you", value: stats.files_shared_with_me },
      ]
    : [];

  const typeEntries = storageStats ? Object.entries(storageStats.by_type) : [];
  const maxTypeBytes = typeEntries.reduce(
    (max, [, info]) => Math.max(max, info.size_bytes),
    0
  );

  return (
    <div>
      <h1 style={{ fontSize: "1.3rem", marginBottom: "1.5rem" }}>Statistics</h1>

      {error && <div className="myfiles__error">{error}</div>}

      {stats && (
        <div className="stats__grid">
          {cards.map((card) => (
            <div key={card.label} className="stats__card">
              <span className="stats__value">{card.value}</span>
              <span className="stats__label">{card.label}</span>
            </div>
          ))}
        </div>
      )}

      {typeEntries.length > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <h2 style={{ fontSize: "1.05rem", marginBottom: "1rem" }}>
            Storage by file type
          </h2>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
            {typeEntries.map(([type, info]) => (
              <div key={type} style={{ display: "flex", alignItems: "center", gap: "0.9rem" }}>
                <span style={{ width: "90px", fontSize: "0.85rem", color: "var(--text-muted)" }}>
                  {TYPE_LABELS[type] || type}
                </span>
                <div
                  style={{
                    flex: 1,
                    background: "var(--surface)",
                    border: "1px solid var(--border)",
                    borderRadius: "6px",
                    height: "10px",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${maxTypeBytes ? (info.size_bytes / maxTypeBytes) * 100 : 0}%`,
                      height: "100%",
                      background: "var(--gold)",
                    }}
                  />
                </div>
                <span style={{ width: "150px", fontSize: "0.8rem", color: "var(--text-muted)", textAlign: "right" }}>
                  {info.count} file{info.count === 1 ? "" : "s"} · {formatBytes(info.size_bytes)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

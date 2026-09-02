import { useEffect, useState } from "react";
import { getStats } from "../../api/files";
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

export default function Statistics() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await getStats();
        if (!cancelled) setStats(data);
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
    </div>
  );
}
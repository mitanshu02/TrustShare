import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { API_BASE_URL } from "../api/client";
import { downloadPublicShareLink, getPublicShareInfo } from "../api/shareLinks";
import "./PublicShare.css";

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

function isPreviewable(contentType) {
  return (
    contentType.startsWith("image/") ||
    contentType === "application/pdf" ||
    contentType.startsWith("text/")
  );
}

export default function PublicShare() {
  const { token } = useParams();
  const [info, setInfo] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await getPublicShareInfo(token);
        if (!cancelled) setInfo(data);
      } catch {
        if (!cancelled) {
          setError(
            "This link is invalid, has expired, been revoked, or reached its download limit.",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [token]);

  async function handleDownload() {
    setDownloading(true);
    setError("");
    try {
      await downloadPublicShareLink(token, info.original_name);
    } catch {
      setError("This link stopped working — it may have just expired or hit its limit.");
    } finally {
      setDownloading(false);
    }
  }

  const previewUrl = `${API_BASE_URL}/api/share/${token}/preview`;
  const canPreview = info && isPreviewable(info.content_type);

  return (
    <div className="public-share">
      <div className={`public-share__card ${canPreview ? "public-share__card--wide" : ""}`}>
        <div className="public-share__mark">TrustShare</div>

        {loading ? (
          <p className="public-share__muted">Checking this link…</p>
        ) : error ? (
          <>
            <svg className="public-share__icon public-share__icon--error" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6" />
              <path d="M9 9l6 6M15 9l-6 6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
            <h1>This link isn't available</h1>
            <p className="public-share__muted">{error}</p>
          </>
        ) : (
          <>
            {!canPreview && (
              <svg className="public-share__icon" viewBox="0 0 24 24" fill="none">
                <path d="M6 3h8l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
                <path d="M14 3v5h5" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
              </svg>
            )}
            <h1>{info.original_name}</h1>
            <p className="public-share__muted">
              {formatBytes(info.size_bytes)} · shared by {info.shared_by_name}
            </p>

            {canPreview && (
              <div className="public-share__preview" onContextMenu={(e) => e.preventDefault()}>
                {info.content_type.startsWith("image/") ? (
                  <img src={previewUrl} alt={info.original_name} draggable="false" />
                ) : (
                  <iframe
                    src={`${previewUrl}#toolbar=0&navpanes=0&scrollbar=0`}
                    title={info.original_name}
                  />
                )}
              </div>
            )}

            {info.access_level === "download" ? (
              <button
                className="public-share__download-btn"
                onClick={handleDownload}
                disabled={downloading}
              >
                {downloading ? "Downloading…" : "Download"}
              </button>
            ) : (
              <p className="public-share__view-only">
                The owner has only allowed viewing this file — downloading isn't enabled for this link.
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
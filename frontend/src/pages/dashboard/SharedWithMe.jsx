import { useEffect, useState } from "react";
import { downloadFile, listSharedWithMe, previewFile } from "../../api/files";
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

function isPreviewable(contentType) {
  return (
    contentType.startsWith("image/") ||
    contentType === "application/pdf" ||
    contentType.startsWith("text/")
  );
}

export default function SharedWithMe() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [openPreview, setOpenPreview] = useState(null); // { fileId, url, contentType }

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

  // Clean up the blob URL whenever the open preview changes or unmounts.
  useEffect(() => {
    return () => {
      if (openPreview) URL.revokeObjectURL(openPreview.url);
    };
  }, [openPreview]);

  async function handleDownload(file) {
    try {
      await downloadFile(file.id, file.original_name);
    } catch {
      setError("Couldn't download that file.");
    }
  }

  async function handleTogglePreview(file) {
    if (openPreview?.fileId === file.id) {
      URL.revokeObjectURL(openPreview.url);
      setOpenPreview(null);
      return;
    }
    try {
      const { url, contentType } = await previewFile(file.id);
      if (openPreview) URL.revokeObjectURL(openPreview.url);
      setOpenPreview({ fileId: file.id, url, contentType });
    } catch {
      setError("Couldn't load a preview for that file.");
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
            <div key={file.id}>
              <div className="myfiles__item">
                <svg className="myfiles__item-icon myfiles__item-icon--file" viewBox="0 0 24 24" fill="none">
                  <path d="M6 3h8l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
                  <path d="M14 3v5h5" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
                </svg>
                <span className="myfiles__item-name">{file.original_name}</span>
                <span className="myfiles__item-meta">
                  {formatBytes(file.size_bytes)} · from {file.shared_by_email} ·{" "}
                  {file.access_level === "download" ? "can download" : "view only"}
                </span>
                <div className="myfiles__item-actions">
                  <button
                    className="myfiles__icon-btn"
                    title="Preview"
                    onClick={() => handleTogglePreview(file)}
                  >
                    <svg viewBox="0 0 24 24" fill="none">
                      <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
                      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.6" />
                    </svg>
                  </button>
                  {file.access_level === "download" && (
                    <button
                      className="myfiles__icon-btn"
                      title="Download"
                      onClick={() => handleDownload(file)}
                    >
                      <svg viewBox="0 0 24 24" fill="none">
                        <path d="M12 4v11m0 0-4-4m4 4 4-4M5 19h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>

              {openPreview?.fileId === file.id && (
                <div className="myfiles__preview-panel">
                  {isPreviewable(openPreview.contentType) ? (
                    openPreview.contentType.startsWith("image/") ? (
                      <img src={openPreview.url} alt={file.original_name} />
                    ) : (
                      <iframe src={openPreview.url} title={file.original_name} />
                    )
                  ) : (
                    <p className="myfiles__preview-unavailable">
                      Preview isn't available for this file type.
                    </p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
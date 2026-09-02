import { useCallback, useEffect, useRef, useState } from "react";
import ShareModal from "../../components/ShareModal";
import {
  createFolder,
  deleteFile,
  downloadFile,
  listFiles,
  listFolders,
  uploadFile,
} from "../../api/files";
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

export default function MyFiles() {
  const fileInputRef = useRef(null);

  const [path, setPath] = useState([]);
  const currentFolderId = path.length ? path[path.length - 1].id : null;

  const [folders, setFolders] = useState([]);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [creatingFolder, setCreatingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");

  const [uploadProgress, setUploadProgress] = useState(null);
  const [shareTarget, setShareTarget] = useState(null);

  const loadContents = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [folderList, fileList] = await Promise.all([
        listFolders(currentFolderId),
        listFiles(currentFolderId),
      ]);
      setFolders(folderList);
      setFiles(fileList);
    } catch {
      setError("Couldn't load your files. Try refreshing the page.");
    } finally {
      setLoading(false);
    }
  }, [currentFolderId]);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      await loadContents();
      if (cancelled) return;
    }
    run();
    return () => {
      cancelled = true;
    };
  }, [loadContents]);

  async function handleCreateFolder(e) {
    e.preventDefault();
    const name = newFolderName.trim();
    if (!name) return;
    try {
      await createFolder({ name, parentFolderId: currentFolderId });
      setNewFolderName("");
      setCreatingFolder(false);
      loadContents();
    } catch {
      setError("Couldn't create that folder. Try again.");
    }
  }

  async function handleFileSelect(e) {
    const selected = e.target.files?.[0];
    e.target.value = "";
    if (!selected) return;

    setUploadProgress(0);
    setError("");
    try {
      await uploadFile({
        file: selected,
        folderId: currentFolderId,
        onProgress: setUploadProgress,
      });
      loadContents();
    } catch {
      setError("Couldn't upload that file. Try again.");
    } finally {
      setUploadProgress(null);
    }
  }

  async function handleDownload(file) {
    try {
      await downloadFile(file.id, file.original_name);
    } catch {
      setError("Couldn't download that file.");
    }
  }

  async function handleDelete(file) {
    if (!window.confirm(`Delete "${file.original_name}"? This can't be undone.`)) {
      return;
    }
    try {
      await deleteFile(file.id);
      loadContents();
    } catch {
      setError("Couldn't delete that file.");
    }
  }

  function openFolder(folder) {
    setPath((prev) => [...prev, { id: folder.id, name: folder.name }]);
  }

  function goToBreadcrumb(index) {
    setPath((prev) => (index < 0 ? [] : prev.slice(0, index + 1)));
  }

  const isEmpty = !loading && folders.length === 0 && files.length === 0;

  return (
    <div>
      <div className="myfiles__breadcrumb">
        <button onClick={() => goToBreadcrumb(-1)}>Home</button>
        {path.map((crumb, i) => (
          <span key={crumb.id} style={{ display: "contents" }}>
            <span>/</span>
            {i === path.length - 1 ? (
              <span className="current">{crumb.name}</span>
            ) : (
              <button onClick={() => goToBreadcrumb(i)}>{crumb.name}</button>
            )}
          </span>
        ))}
      </div>

      {error && <div className="myfiles__error">{error}</div>}

      <div className="myfiles__toolbar">
        <button className="myfiles__btn" onClick={() => setCreatingFolder((v) => !v)}>
          New folder
        </button>
        <button
          className="myfiles__btn myfiles__btn--primary"
          onClick={() => fileInputRef.current?.click()}
        >
          Upload file
        </button>
        <input
          ref={fileInputRef}
          type="file"
          style={{ display: "none" }}
          onChange={handleFileSelect}
        />
      </div>

      {creatingFolder && (
        <form className="myfiles__inline-form" onSubmit={handleCreateFolder}>
          <input
            type="text"
            placeholder="Folder name"
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            autoFocus
          />
          <button className="myfiles__btn myfiles__btn--primary" type="submit">
            Create
          </button>
        </form>
      )}

      {uploadProgress !== null && (
        <div className="myfiles__progress">
          <div
            className="myfiles__progress-bar"
            style={{ width: `${uploadProgress}%` }}
          />
        </div>
      )}

      {loading ? (
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Loading…</p>
      ) : isEmpty ? (
        <div className="myfiles__empty">
          <svg className="myfiles__empty-icon" viewBox="0 0 64 64" fill="none">
            <rect x="14" y="28" width="36" height="28" rx="4" stroke="currentColor" strokeWidth="2.5" />
            <path d="M22 28V20a10 10 0 0 1 20 0v8" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" fill="none" />
          </svg>
          <h2>Nothing here yet</h2>
          <p>Create a folder or upload a file — everything is encrypted with AES-256 before it's stored.</p>
        </div>
      ) : (
        <>
          {folders.length > 0 && (
            <>
              <p className="myfiles__section-label">Folders</p>
              <div className="myfiles__list">
                {folders.map((folder) => (
                  <button
                    key={folder.id}
                    className="myfiles__item myfiles__item--folder"
                    onClick={() => openFolder(folder)}
                  >
                    <svg className="myfiles__item-icon" viewBox="0 0 24 24" fill="none">
                      <path d="M3 6a1 1 0 0 1 1-1h5l2 2h9a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
                    </svg>
                    <span className="myfiles__item-name">{folder.name}</span>
                  </button>
                ))}
              </div>
            </>
          )}

          {files.length > 0 && (
            <>
              <p className="myfiles__section-label">Files</p>
              <div className="myfiles__list">
                {files.map((file) => (
                  <div key={file.id} className="myfiles__item">
                    <svg className="myfiles__item-icon myfiles__item-icon--file" viewBox="0 0 24 24" fill="none">
                      <path d="M6 3h8l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
                      <path d="M14 3v5h5" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
                    </svg>
                    <span className="myfiles__item-name">{file.original_name}</span>
                    <span className="myfiles__item-meta">{formatBytes(file.size_bytes)}</span>
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
                      <button
                        className="myfiles__icon-btn"
                        title="Share"
                        onClick={() => setShareTarget(file)}
                      >
                        <svg viewBox="0 0 24 24" fill="none">
                          <circle cx="6" cy="12" r="2.2" stroke="currentColor" strokeWidth="1.6" />
                          <circle cx="18" cy="6" r="2.2" stroke="currentColor" strokeWidth="1.6" />
                          <circle cx="18" cy="18" r="2.2" stroke="currentColor" strokeWidth="1.6" />
                          <path d="M8 10.8 16 7.2M8 13.2l8 3.6" stroke="currentColor" strokeWidth="1.6" />
                        </svg>
                      </button>
                      <button
                        className="myfiles__icon-btn myfiles__icon-btn--danger"
                        title="Delete"
                        onClick={() => handleDelete(file)}
                      >
                        <svg viewBox="0 0 24 24" fill="none">
                          <path d="M5 7h14M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2m-8 0 1 12a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1l1-12" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}

      {shareTarget && (
        <ShareModal file={shareTarget} onClose={() => setShareTarget(null)} />
      )}
    </div>
  );
}
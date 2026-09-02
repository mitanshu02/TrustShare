import { useEffect, useState } from "react";
import {
  listPermissions,
  revokePermission,
  shareFile,
  updatePermission,
} from "../api/files";
import "./ShareModal.css";

export default function ShareModal({ file, onClose }) {
  const [emailsInput, setEmailsInput] = useState("");
  const [accessLevel, setAccessLevel] = useState("view");
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function loadPermissions() {
    setLoading(true);
    try {
      const data = await listPermissions(file.id);
      setPermissions(data);
    } catch {
      setError("Couldn't load who this is shared with.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    async function run() {
      await loadPermissions();
      if (cancelled) return;
    }
    run();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file.id]);

  async function handleShare(e) {
    e.preventDefault();
    setError("");
    setNotice("");

    const emails = emailsInput
      .split(/[,\s]+/)
      .map((e) => e.trim())
      .filter(Boolean);

    if (emails.length === 0) {
      setError("Enter at least one email address.");
      return;
    }

    setSubmitting(true);
    try {
      const result = await shareFile({ fileId: file.id, emails, accessLevel });
      if (result.not_found.length > 0) {
        setNotice(
          `Shared with ${result.shared_with.length} ${result.shared_with.length === 1 ? "person" : "people"}. No account found for: ${result.not_found.join(", ")}.`,
        );
      } else {
        setNotice(`Shared with ${result.shared_with.length} ${result.shared_with.length === 1 ? "person" : "people"}.`);
      }
      setEmailsInput("");
      loadPermissions();
    } catch {
      setError("Couldn't share this file. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleLevelChange(permissionId, newLevel) {
    try {
      await updatePermission({ fileId: file.id, permissionId, accessLevel: newLevel });
      loadPermissions();
    } catch {
      setError("Couldn't update that person's access.");
    }
  }

  async function handleRevoke(permissionId) {
    try {
      await revokePermission({ fileId: file.id, permissionId });
      loadPermissions();
    } catch {
      setError("Couldn't revoke access.");
    }
  }

  return (
    <div className="share-modal__backdrop" onClick={onClose}>
      <div className="share-modal" onClick={(e) => e.stopPropagation()}>
        <div className="share-modal__header">
          <h3>Share "{file.original_name}"</h3>
          <button className="share-modal__close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        {error && <div className="share-modal__error">{error}</div>}
        {notice && <div className="share-modal__notice">{notice}</div>}

        <form className="share-modal__form" onSubmit={handleShare}>
          <input
            type="text"
            placeholder="Email addresses, separated by commas"
            value={emailsInput}
            onChange={(e) => setEmailsInput(e.target.value)}
          />
          <select value={accessLevel} onChange={(e) => setAccessLevel(e.target.value)}>
            <option value="view">Can view</option>
            <option value="download">Can download</option>
          </select>
          <button type="submit" disabled={submitting}>
            {submitting ? "Sharing…" : "Share"}
          </button>
        </form>

        <p className="share-modal__section-label">People with access</p>
        {loading ? (
          <p className="share-modal__muted">Loading…</p>
        ) : permissions.length === 0 ? (
          <p className="share-modal__muted">Not shared with anyone yet.</p>
        ) : (
          <ul className="share-modal__list">
            {permissions.map((p) => (
              <li key={p.id} className="share-modal__list-item">
                <span className="share-modal__email">{p.user_email}</span>
                <select
                  value={p.access_level}
                  onChange={(e) => handleLevelChange(p.id, e.target.value)}
                >
                  <option value="view">Can view</option>
                  <option value="download">Can download</option>
                </select>
                <button
                  className="share-modal__revoke"
                  onClick={() => handleRevoke(p.id)}
                  type="button"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
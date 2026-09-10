import { useEffect, useState } from "react";
import {
  listPermissions,
  revokePermission,
  shareFile,
  updatePermission,
} from "../api/files";
import {
  createShareLink,
  listShareLinks,
  revokeShareLink,
} from "../api/shareLinks";
import "./ShareModal.css";

function LinkTab({ file }) {
  const [links, setLinks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [justCreated, setJustCreated] = useState(null); // { token, ...link }

  const [accessLevel, setAccessLevel] = useState("download");
  const [expiresInHours, setExpiresInHours] = useState(24);
  const [maxDownloads, setMaxDownloads] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [copied, setCopied] = useState(false);

  async function loadLinks() {
    setLoading(true);
    try {
      const data = await listShareLinks(file.id);
      setLinks(data);
    } catch {
      setError("Couldn't load existing links.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    async function run() {
      await loadLinks();
      if (cancelled) return;
    }
    run();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file.id]);

  async function handleCreate(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const created = await createShareLink({
        fileId: file.id,
        accessLevel,
        expiresInHours: Number(expiresInHours),
        maxDownloads: maxDownloads ? Number(maxDownloads) : null,
      });
      setJustCreated(created);
      loadLinks();
    } catch {
      setError("Couldn't create a link. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRevoke(linkId) {
    try {
      await revokeShareLink({ fileId: file.id, linkId });
      loadLinks();
    } catch {
      setError("Couldn't revoke that link.");
    }
  }

  function shareUrl(token) {
    return `${window.location.origin}/share/${token}`;
  }

  async function copyLink(token) {
    try {
      await navigator.clipboard.writeText(shareUrl(token));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API can fail (permissions, non-secure context); the
      // link is still visible on screen to copy manually.
    }
  }

  return (
    <>
      {error && <div className="share-modal__error">{error}</div>}

      {justCreated && (
        <div className="share-modal__link-created">
          <p>Link created — copy it now, it won't be shown again:</p>
          <div className="share-modal__link-row">
            <input readOnly value={shareUrl(justCreated.token)} onFocus={(e) => e.target.select()} />
            <button
              type="button"
              className={copied ? "share-modal__copy-btn--copied" : ""}
              onClick={() => copyLink(justCreated.token)}
            >
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
        </div>
      )}

      <form className="share-modal__form" onSubmit={handleCreate}>
        <select value={accessLevel} onChange={(e) => setAccessLevel(e.target.value)}>
          <option value="view">Anyone with the link can view</option>
          <option value="download">Anyone with the link can download</option>
        </select>
        <div className="share-modal__link-row">
          <input
            type="number"
            min="1"
            max="720"
            value={expiresInHours}
            onChange={(e) => setExpiresInHours(e.target.value)}
            title="Expires in (hours)"
          />
          <span className="share-modal__inline-label">hours until it expires</span>
        </div>
        <input
          type="number"
          min="1"
          placeholder="Max downloads (optional)"
          value={maxDownloads}
          onChange={(e) => setMaxDownloads(e.target.value)}
        />
        <button type="submit" disabled={submitting}>
          {submitting ? "Creating…" : "Create link"}
        </button>
      </form>

      <p className="share-modal__section-label">Active links</p>
      {loading ? (
        <p className="share-modal__muted">Loading…</p>
      ) : links.filter((l) => l.is_active).length === 0 ? (
        <p className="share-modal__muted">No active links.</p>
      ) : (
        <ul className="share-modal__list">
          {links
            .filter((l) => l.is_active)
            .map((l) => (
              <li key={l.id} className="share-modal__list-item">
                <span className="share-modal__email">
                  {l.access_level === "download" ? "Can download" : "Can view"} ·{" "}
                  {l.download_count}
                  {l.max_downloads ? `/${l.max_downloads}` : ""} used · expires{" "}
                  {new Date(l.expires_at).toLocaleDateString()}
                </span>
                <button
                  className="share-modal__revoke"
                  onClick={() => handleRevoke(l.id)}
                  type="button"
                >
                  Revoke
                </button>
              </li>
            ))}
        </ul>
      )}
    </>
  );
}

function EmailTab({ file }) {
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
    <>
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
    </>
  );
}

export default function ShareModal({ file, onClose }) {
  const [tab, setTab] = useState("email"); // "email" | "link"

  return (
    <div className="share-modal__backdrop" onClick={onClose}>
      <div className="share-modal" onClick={(e) => e.stopPropagation()}>
        <div className="share-modal__header">
          <h3>Share "{file.original_name}"</h3>
          <button className="share-modal__close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        <div className="share-modal__tabs">
          <button
            className={tab === "email" ? "active" : ""}
            onClick={() => setTab("email")}
            type="button"
          >
            By email
          </button>
          <button
            className={tab === "link" ? "active" : ""}
            onClick={() => setTab("link")}
            type="button"
          >
            By link
          </button>
        </div>

        {tab === "email" ? <EmailTab file={file} /> : <LinkTab file={file} />}
      </div>
    </div>
  );
}
import { useEffect, useState } from "react";
import RoleChangeModal from "../../components/RoleChangeModal";
import {
  getPlatformStats,
  getRoleAudit,
  listAllFiles,
  listAllUsers,
  updateUserStatus,
} from "../../api/admin";
import "./Admin.css";

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

export default function Admin() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [files, setFiles] = useState([]);
  const [audit, setAudit] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [roleModal, setRoleModal] = useState(null); // { user, newRole }

  async function loadAll() {
    setLoading(true);
    setError("");
    try {
      const [statsData, usersData, filesData, auditData] = await Promise.all([
        getPlatformStats(),
        listAllUsers(),
        listAllFiles(),
        getRoleAudit(),
      ]);
      setStats(statsData);
      setUsers(usersData);
      setFiles(filesData);
      setAudit(auditData);
    } catch {
      setError("Couldn't load admin data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    async function run() {
      await loadAll();
      if (cancelled) return;
    }
    run();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleToggleStatus(user) {
    const newStatus = user.account_status === "active" ? "inactive" : "active";
    try {
      await updateUserStatus({ userId: user.id, accountStatus: newStatus });
      loadAll();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(detail || "Couldn't update that user's status.");
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: "1.3rem", marginBottom: "1.5rem" }}>Admin</h1>

      {error && <div className="myfiles__error">{error}</div>}

      {loading ? (
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Loading…</p>
      ) : (
        <>
          {stats && (
            <div className="stats__grid" style={{ marginBottom: "2rem" }}>
              <div className="stats__card">
                <span className="stats__value">{stats.total_users}</span>
                <span className="stats__label">Total users</span>
              </div>
              <div className="stats__card">
                <span className="stats__value">{stats.total_files}</span>
                <span className="stats__label">Total files</span>
              </div>
              <div className="stats__card">
                <span className="stats__value">{formatBytes(stats.total_storage_bytes)}</span>
                <span className="stats__label">Total storage</span>
              </div>
              <div className="stats__card">
                <span className="stats__value">{stats.total_shares}</span>
                <span className="stats__label">Active shares</span>
              </div>
            </div>
          )}

          <p className="myfiles__section-label" style={{ marginTop: 0 }}>Users</p>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th></th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.full_name}</td>
                  <td>{u.email}</td>
                  <td>{u.role}</td>
                  <td>
                    <span className={`admin-badge admin-badge--${u.account_status}`}>
                      {u.account_status}
                    </span>
                  </td>
                  <td>
                    <button
                      className="myfiles__btn"
                      style={{ padding: "0.3rem 0.7rem", fontSize: "0.78rem" }}
                      onClick={() =>
                        setRoleModal({ user: u, newRole: u.role === "admin" ? "user" : "admin" })
                      }
                    >
                      {u.role === "admin" ? "Remove admin" : "Make admin"}
                    </button>
                  </td>
                  <td>
                    <button
                      className="myfiles__btn"
                      style={{ padding: "0.3rem 0.7rem", fontSize: "0.78rem" }}
                      onClick={() => handleToggleStatus(u)}
                    >
                      {u.account_status === "active" ? "Deactivate" : "Activate"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <p className="myfiles__section-label">All files on the platform</p>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Owner</th>
                <th>Size</th>
                <th>Uploaded</th>
              </tr>
            </thead>
            <tbody>
              {files.map((f) => (
                <tr key={f.id}>
                  <td>{f.original_name}</td>
                  <td>{f.owner_email}</td>
                  <td>{formatBytes(f.size_bytes)}</td>
                  <td>{new Date(f.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <p className="myfiles__section-label">Role change history</p>
          {audit.length === 0 ? (
            <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
              No role changes have been made yet.
            </p>
          ) : (
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Changed by</th>
                  <th>User</th>
                  <th>Change</th>
                  <th>When</th>
                </tr>
              </thead>
              <tbody>
                {audit.map((a) => (
                  <tr key={a.id}>
                    <td>{a.changed_by_email}</td>
                    <td>{a.target_user_email}</td>
                    <td>
                      {a.old_role} → {a.new_role}
                    </td>
                    <td>{new Date(a.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}

      {roleModal && (
        <RoleChangeModal
          user={roleModal.user}
          newRole={roleModal.newRole}
          onClose={() => setRoleModal(null)}
          onSuccess={() => {
            setRoleModal(null);
            loadAll();
          }}
        />
      )}
    </div>
  );
}
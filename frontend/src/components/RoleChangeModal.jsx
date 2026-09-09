import { useState } from "react";
import { changeUserRole } from "../api/admin";
import "./RoleChangeModal.css";

export default function RoleChangeModal({ user, newRole, onClose, onSuccess }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleConfirm(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await changeUserRole({ userId: user.id, newRole, currentPassword: password });
      onSuccess();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(detail || "Couldn't change that user's role.");
    } finally {
      setSubmitting(false);
    }
  }

  const isPromotion = newRole === "admin";

  return (
    <div className="role-modal__backdrop" onClick={onClose}>
      <div className="role-modal" onClick={(e) => e.stopPropagation()}>
        <h3>
          {isPromotion ? "Make " : "Remove admin access from "}
          <span className="role-modal__name">{user.full_name}</span>
          {isPromotion ? " an admin?" : "?"}
        </h3>
        <p className="role-modal__warning">
          {isPromotion
            ? "This grants full platform access, including managing other users' accounts and viewing all files. This action is logged."
            : "They will immediately lose admin access. This action is logged."}
        </p>

        {error && <div className="role-modal__error">{error}</div>}

        <form onSubmit={handleConfirm}>
          <label className="role-modal__label" htmlFor="confirm-password">
            Confirm your password to continue
          </label>
          <input
            id="confirm-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoFocus
          />

          <div className="role-modal__actions">
            <button type="button" className="role-modal__cancel" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className={
                isPromotion ? "role-modal__confirm" : "role-modal__confirm role-modal__confirm--danger"
              }
              disabled={submitting}
            >
              {submitting ? "Confirming…" : isPromotion ? "Make admin" : "Remove admin"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
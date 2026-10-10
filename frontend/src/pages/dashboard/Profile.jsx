import { useState } from "react";
import { changePassword, updateProfile } from "../../api/auth";
import { useAuth } from "../../context/useAuth";
import "./Account.css";

function initialsOf(name) {
  return (name || "?")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}

function errorText(err, fallback) {
  const detail = err?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}

export default function Profile() {
  const { user, updateUser } = useAuth();

  const [fullName, setFullName] = useState(user?.full_name || "");
  const [profileState, setProfileState] = useState({ busy: false, ok: "", error: "" });

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordState, setPasswordState] = useState({ busy: false, ok: "", error: "" });

  const nameChanged = fullName.trim() && fullName.trim() !== user?.full_name;

  async function handleProfileSubmit(event) {
    event.preventDefault();
    setProfileState({ busy: true, ok: "", error: "" });
    try {
      const updated = await updateProfile({ fullName: fullName.trim() });
      updateUser({ full_name: updated.full_name });
      setProfileState({ busy: false, ok: "Name updated.", error: "" });
    } catch (err) {
      setProfileState({ busy: false, ok: "", error: errorText(err, "Couldn't update your name. Try again.") });
    }
  }

  async function handlePasswordSubmit(event) {
    event.preventDefault();
    if (newPassword !== confirmPassword) {
      setPasswordState({ busy: false, ok: "", error: "The new passwords don't match." });
      return;
    }
    setPasswordState({ busy: true, ok: "", error: "" });
    try {
      await changePassword({ currentPassword, newPassword });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordState({ busy: false, ok: "Password changed.", error: "" });
    } catch (err) {
      setPasswordState({
        busy: false,
        ok: "",
        error: errorText(err, "Couldn't change your password. Check the new password is at least 8 characters."),
      });
    }
  }

  if (!user) return null;

  return (
    <div className="account">
      <div>
        <h1 className="account__title">Profile</h1>
        <p className="account__subtitle">Your account details and sign-in security.</p>
      </div>

      <section className="account__card">
        <div className="account__identity">
          <div className="account__avatar" aria-hidden="true">{initialsOf(user.full_name)}</div>
          <div>
            <div className="account__name">{user.full_name}</div>
            <div className="account__email">{user.email}</div>
            <div className="account__meta">
              <span className="account__chip account__chip--role">
                {user.role === "admin" ? "Administrator" : "Member"}
              </span>
              <span className="account__chip">
                Joined {new Date(user.created_at).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" })}
              </span>
            </div>
          </div>
        </div>
      </section>

      <section className="account__card">
        <h2>Personal details</h2>
        <p className="account__card-hint">Your email is your sign-in and can't be changed here.</p>
        <form className="account__form" onSubmit={handleProfileSubmit}>
          <div className="account__field">
            <label htmlFor="profile-name">Full name</label>
            <input
              id="profile-name"
              className="account__input"
              value={fullName}
              maxLength={150}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>
          <div className="account__field">
            <label htmlFor="profile-email">Email</label>
            <input id="profile-email" className="account__input" value={user.email} disabled />
          </div>
          <div className="account__actions">
            <button className="account__button" type="submit" disabled={!nameChanged || profileState.busy}>
              {profileState.busy ? "Saving…" : "Save changes"}
            </button>
            {profileState.ok && <span className="account__message account__message--ok">{profileState.ok}</span>}
            {profileState.error && <span className="account__message account__message--error">{profileState.error}</span>}
          </div>
        </form>
      </section>

      <section className="account__card">
        <h2>Change password</h2>
        <p className="account__card-hint">Use at least 8 characters. You'll get a notification confirming the change.</p>
        <form className="account__form" onSubmit={handlePasswordSubmit}>
          <div className="account__field">
            <label htmlFor="current-password">Current password</label>
            <input id="current-password" type="password" autoComplete="current-password" className="account__input"
              value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required />
          </div>
          <div className="account__field">
            <label htmlFor="new-password">New password</label>
            <input id="new-password" type="password" autoComplete="new-password" minLength={8} className="account__input"
              value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required />
          </div>
          <div className="account__field">
            <label htmlFor="confirm-password">Confirm new password</label>
            <input id="confirm-password" type="password" autoComplete="new-password" minLength={8} className="account__input"
              value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required />
          </div>
          <div className="account__actions">
            <button className="account__button" type="submit" disabled={passwordState.busy}>
              {passwordState.busy ? "Updating…" : "Update password"}
            </button>
            {passwordState.ok && <span className="account__message account__message--ok">{passwordState.ok}</span>}
            {passwordState.error && <span className="account__message account__message--error">{passwordState.error}</span>}
          </div>
        </form>
      </section>
    </div>
  );
}

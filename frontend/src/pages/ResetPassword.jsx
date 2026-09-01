import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import BrandPanel from "../components/BrandPanel";
import { resetPassword } from "../api/auth";
import "./Auth.css";

export default function ResetPassword() {
  const navigate = useNavigate();
  const location = useLocation();
  const prefillEmail = location.state?.email || "";

  const [email, setEmail] = useState(prefillEmail);
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState("");
  const [status, setStatus] = useState("idle"); // idle | submitting | success

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    if (!/^\d{6}$/.test(otp)) {
      setError("Enter the 6-digit code exactly as you received it.");
      return;
    }

    setStatus("submitting");
    try {
      await resetPassword({ email, otp, newPassword });
      setStatus("success");
      setTimeout(() => navigate("/login"), 1200);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(detail || "That code didn't work. Request a new one and try again.");
      setStatus("idle");
    }
  }

  return (
    <div className="auth-shell">
      <BrandPanel
        headline="One code, one use, ten minutes."
        body="Each code works exactly once and expires quickly — so a leaked code is only ever a narrow window, not a standing risk."
      />

      <div className="auth-form-panel">
        <div className="auth-card">
          <h2>Enter your code</h2>
          <p className="auth-subtitle">
            Check your email for the 6-digit verification code
          </p>

          {error && <div className="auth-error">{error}</div>}

          {status === "success" ? (
            <div
              className="auth-error"
              style={{
                background: "var(--teal-soft)",
                borderColor: "var(--teal)",
                color: "var(--text)",
              }}
            >
              Password reset. Taking you to log in…
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="auth-field">
                <label htmlFor="email">Email</label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                />
              </div>

              <div className="auth-field">
                <label htmlFor="otp">6-digit code</label>
                <input
                  id="otp"
                  type="text"
                  inputMode="numeric"
                  pattern="\d{6}"
                  maxLength={6}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
                  required
                  autoComplete="one-time-code"
                  style={{ letterSpacing: "0.3em", fontFamily: "var(--font-mono)" }}
                />
              </div>

              <div className="auth-field">
                <label htmlFor="newPassword">New password</label>
                <input
                  id="newPassword"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={8}
                  autoComplete="new-password"
                />
              </div>

              <button
                className="auth-submit"
                type="submit"
                disabled={status === "submitting"}
              >
                {status === "submitting" ? "Resetting…" : "Reset password"}
              </button>
            </form>
          )}

          <p className="auth-switch">
            Didn't get a code? <Link to="/forgot-password">Request another</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
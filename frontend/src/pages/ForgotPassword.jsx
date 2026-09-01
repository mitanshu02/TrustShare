import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import BrandPanel from "../components/BrandPanel";
import { forgotPassword } from "../api/auth";
import "./Auth.css";

export default function ForgotPassword() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [status, setStatus] = useState("idle"); // idle | submitting | sent

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setStatus("submitting");
    try {
      await forgotPassword({ email });
      setStatus("sent");
    } catch {
      setError("Something went wrong. Please try again.");
      setStatus("idle");
    }
  }

  return (
    <div className="auth-shell">
      <BrandPanel
        headline="Locked out? That's the point."
        body="Your password never leaves your device unhashed — not even we can look it up. A one-time code is the only way back in."
      />

      <div className="auth-form-panel">
        <div className="auth-card">
          <h2>Reset your password</h2>
          <p className="auth-subtitle">
            Enter your email and we'll send a 6-digit code
          </p>

          {error && <div className="auth-error">{error}</div>}

          {status === "sent" ? (
            <>
              <div className="auth-error" style={{ background: "var(--teal-soft)", borderColor: "var(--teal)", color: "var(--text)" }}>
                If an account exists for that email, a code is on its way.
                Check your inbox — it expires in 10 minutes.
              </div>
              <button
                className="auth-submit"
                type="button"
                onClick={() =>
                  navigate("/reset-password", { state: { email } })
                }
              >
                I have a code
              </button>
            </>
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

              <button
                className="auth-submit"
                type="submit"
                disabled={status === "submitting"}
              >
                {status === "submitting" ? "Sending…" : "Send code"}
              </button>
            </form>
          )}

          <p className="auth-switch">
            Remembered your password? <Link to="/login">Log in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
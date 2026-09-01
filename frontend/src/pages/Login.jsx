import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import BrandPanel from "../components/BrandPanel";
import { useAuth } from "../context/useAuth";
import "./Auth.css";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [status, setStatus] = useState("idle"); // idle | submitting | success

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setStatus("submitting");
    try {
      await login({ email, password });
      setStatus("success");
      setTimeout(() => navigate("/dashboard"), 450);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(detail || "That email and password combination didn't work.");
      setStatus("idle");
    }
  }

  return (
    <div className="auth-shell">
      <BrandPanel
        headline="Every file, sealed before it leaves your hands."
        body="TrustShare encrypts each upload with AES-256 the moment it arrives, and only the people you approve can ever open it."
      />

      <div className="auth-form-panel">
        <div className="auth-card">
          <h2>Welcome back</h2>
          <p className="auth-subtitle">Log in to your TrustShare account</p>

          {error && <div className="auth-error">{error}</div>}

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
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
              <p style={{ marginTop: "0.5rem", fontSize: "0.8rem" }}>
                <Link to="/forgot-password" style={{ color: "var(--gold)", textDecoration: "none" }}>
                  Forgot your password?
                </Link>
              </p>
            </div>

            <button
              className="auth-submit"
              type="submit"
              disabled={status !== "idle"}
            >
              {status === "success" ? (
                <svg
                  className="auth-submit__check"
                  viewBox="0 0 20 20"
                  fill="none"
                >
                  <path
                    d="M4 10.5l4 4 8-9"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              ) : status === "submitting" ? (
                "Logging in…"
              ) : (
                "Log in"
              )}
            </button>
          </form>

          <p className="auth-switch">
            Don't have an account? <Link to="/register">Sign up</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
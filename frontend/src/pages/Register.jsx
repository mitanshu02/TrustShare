import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import BrandPanel from "../components/BrandPanel";
import { useAuth } from "../context/useAuth";
import "./Auth.css";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [status, setStatus] = useState("idle"); // idle | submitting | success

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    setStatus("submitting");
    try {
      await register({ fullName, email, password });
      setStatus("success");
      setTimeout(() => navigate("/dashboard"), 450);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(detail || "Registration failed. Please try again.");
      setStatus("idle");
    }
  }

  return (
    <div className="auth-shell">
      <BrandPanel
        headline="Start keeping your files to yourself."
        body="Every file you upload gets its own encryption key — generated per file, never shared, never guessable."
      />

      <div className="auth-form-panel">
        <div className="auth-card">
          <h2>Create your account</h2>
          <p className="auth-subtitle">
            Start sharing files securely with TrustShare
          </p>

          {error && <div className="auth-error">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="auth-field">
              <label htmlFor="fullName">Full name</label>
              <input
                id="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                autoComplete="name"
              />
            </div>

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
                minLength={8}
                autoComplete="new-password"
              />
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
                "Creating account…"
              ) : (
                "Sign up"
              )}
            </button>
          </form>

          <p className="auth-switch">
            Already have an account? <Link to="/login">Log in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
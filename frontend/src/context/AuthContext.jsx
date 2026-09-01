import { useEffect, useState } from "react";
import { fetchCurrentUser, loginUser, registerUser } from "../api/auth";
import { AuthContext } from "./authContextObject";

const TOKEN_KEY = "trustshare_token";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // On first load, if a token exists, try to restore the session.
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);

    async function restoreSession() {
      if (!token) {
        return;
      }
      try {
        const currentUser = await fetchCurrentUser();
        setUser(currentUser);
      } catch {
        // Token is invalid/expired — clear it.
        localStorage.removeItem(TOKEN_KEY);
        setUser(null);
      }
    }

    restoreSession().finally(() => setLoading(false));
  }, []);

  async function login({ email, password }) {
    const { access_token: token } = await loginUser({ email, password });
    localStorage.setItem(TOKEN_KEY, token);
    const currentUser = await fetchCurrentUser();
    setUser(currentUser);
    return currentUser;
  }

  async function register({ fullName, email, password }) {
    await registerUser({ fullName, email, password });
    // Registration succeeded; log the user in immediately for a smooth flow.
    return login({ email, password });
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  }

  const value = {
    user,
    isAuthenticated: Boolean(user),
    loading,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
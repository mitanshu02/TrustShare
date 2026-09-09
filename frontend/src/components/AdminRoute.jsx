import { Navigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";

export default function AdminRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <p style={{ textAlign: "center", marginTop: "3rem" }}>Loading…</p>;
  }

  if (user?.role !== "admin") {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}
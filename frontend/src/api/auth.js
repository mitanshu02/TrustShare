import apiClient from "./client";

export async function registerUser({ fullName, email, password }) {
  const response = await apiClient.post("/api/auth/register", {
    full_name: fullName,
    email,
    password,
  });
  return response.data;
}

export async function loginUser({ email, password }) {
  const response = await apiClient.post("/api/auth/login", {
    email,
    password,
  });
  return response.data; // { access_token, token_type }
}

export async function fetchCurrentUser() {
  const response = await apiClient.get("/api/auth/me");
  return response.data;
}

export async function forgotPassword({ email }) {
  const response = await apiClient.post("/api/auth/forgot-password", { email });
  return response.data; // { message }
}

export async function resetPassword({ email, otp, newPassword }) {
  const response = await apiClient.post("/api/auth/reset-password", {
    email,
    otp,
    new_password: newPassword,
  });
  return response.data; // { message }
}
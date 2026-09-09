import apiClient from "./client";

export async function listAllUsers() {
  const response = await apiClient.get("/api/admin/users");
  return response.data;
}

export async function updateUserStatus({ userId, accountStatus }) {
  const response = await apiClient.patch(`/api/admin/users/${userId}/status`, {
    account_status: accountStatus,
  });
  return response.data;
}

export async function listAllFiles() {
  const response = await apiClient.get("/api/admin/files");
  return response.data;
}

export async function getPlatformStats() {
  const response = await apiClient.get("/api/admin/stats");
  return response.data;
}


export async function changeUserRole({ userId, newRole, currentPassword }) {
  const response = await apiClient.patch(`/api/admin/users/${userId}/role`, {
    new_role: newRole,
    current_password: currentPassword,
  });
  return response.data;
}

export async function getRoleAudit() {
  const response = await apiClient.get("/api/admin/audit/roles");
  return response.data;
}
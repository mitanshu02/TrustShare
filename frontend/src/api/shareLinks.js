import apiClient from "./client";

export async function createShareLink({ fileId, accessLevel, expiresInHours, maxDownloads }) {
  const response = await apiClient.post(`/api/files/${fileId}/links`, {
    access_level: accessLevel,
    expires_in_hours: expiresInHours,
    max_downloads: maxDownloads || null,
  });
  return response.data; // includes raw token, shown once
}

export async function listShareLinks(fileId) {
  const response = await apiClient.get(`/api/files/${fileId}/links`);
  return response.data;
}

export async function revokeShareLink({ fileId, linkId }) {
  await apiClient.delete(`/api/files/${fileId}/links/${linkId}`);
}

// --- Public endpoints (no auth required) ---

export async function getPublicShareInfo(token) {
  const response = await apiClient.get(`/api/share/${token}`);
  return response.data;
}

export async function downloadPublicShareLink(token, fileName) {
  const response = await apiClient.get(`/api/share/${token}/download`, {
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
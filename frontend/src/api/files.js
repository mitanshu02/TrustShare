import apiClient from "./client";

export async function listFolders(parentFolderId) {
  const params = parentFolderId ? { parent_folder_id: parentFolderId } : {};
  const response = await apiClient.get("/api/folders", { params });
  return response.data;
}

export async function createFolder({ name, parentFolderId }) {
  const response = await apiClient.post("/api/folders", {
    name,
    parent_folder_id: parentFolderId ?? null,
  });
  return response.data;
}

export async function listFiles(folderId) {
  const params = folderId ? { folder_id: folderId } : {};
  const response = await apiClient.get("/api/files", { params });
  return response.data;
}

export async function uploadFile({ file, folderId, onProgress }) {
  const formData = new FormData();
  formData.append("file", file);
  if (folderId) formData.append("folder_id", folderId);

  const response = await apiClient.post("/api/files/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: onProgress
      ? (evt) => onProgress(Math.round((evt.loaded / evt.total) * 100))
      : undefined,
  });
  return response.data;
}

export async function downloadFile(fileId, fileName) {
  const response = await apiClient.get(`/api/files/${fileId}/download`, {
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

export async function deleteFile(fileId) {
  await apiClient.delete(`/api/files/${fileId}`);
}

export async function shareFile({ fileId, emails, accessLevel }) {
  const response = await apiClient.post(`/api/files/${fileId}/share`, {
    emails,
    access_level: accessLevel,
  });
  return response.data;
}

export async function listPermissions(fileId) {
  const response = await apiClient.get(`/api/files/${fileId}/permissions`);
  return response.data;
}

export async function updatePermission({ fileId, permissionId, accessLevel }) {
  const response = await apiClient.patch(
    `/api/files/${fileId}/permissions/${permissionId}`,
    { access_level: accessLevel },
  );
  return response.data;
}

export async function revokePermission({ fileId, permissionId }) {
  await apiClient.delete(`/api/files/${fileId}/permissions/${permissionId}`);
}

export async function listSharedWithMe() {
  const response = await apiClient.get("/api/files/shared-with-me");
  return response.data;
}

export async function getActivity() {
  const response = await apiClient.get("/api/activity");
  return response.data;
}

export async function getStats() {
  const response = await apiClient.get("/api/stats");
  return response.data;
}
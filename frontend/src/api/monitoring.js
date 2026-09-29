import apiClient from "./client";

export async function getNotifications({ limit = 50, offset = 0 } = {}) {
  const response = await apiClient.get("/api/notifications", {
    params: { limit, offset },
  });
  return response.data;
}

export async function getUnreadNotificationCount() {
  const response = await apiClient.get("/api/notifications/unread-count");
  return response.data.unread_count;
}

export async function markNotificationRead(notificationId) {
  await apiClient.patch(`/api/notifications/${notificationId}/read`);
}

export async function markAllNotificationsRead() {
  await apiClient.patch("/api/notifications/read-all");
}

export async function getSecurityAnalytics() {
  const response = await apiClient.get("/api/admin/security-analytics");
  return response.data;
}
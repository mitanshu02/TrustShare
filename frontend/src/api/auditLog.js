import apiClient from "./client";

export async function getAuditLog({
  category,
  eventType,
  q,
  dateFrom,
  dateTo,
  limit = 100,
  offset = 0,
} = {}) {
  const response = await apiClient.get("/api/audit-log", {
    params: {
      category: category || undefined,
      event_type: eventType || undefined,
      q: q || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      limit,
      offset,
    },
  });
  return response.data;
}

export async function exportAuditLog({ category, eventType, q, dateFrom, dateTo } = {}) {
  const response = await apiClient.get("/api/audit-log/export", {
    params: {
      category: category || undefined,
      event_type: eventType || undefined,
      q: q || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    },
    responseType: "blob",
  });

  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.download = "trustshare-audit-log.csv";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export async function getSecurityStatus() {
  const response = await apiClient.get("/api/security-status");
  return response.data;
}

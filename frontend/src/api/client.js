import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("talentsync_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function getApiErrorMessage(
  error,
  fallback = "Ocurrió un error inesperado",
) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (typeof item === "string" ? item : item?.msg))
      .filter(Boolean);
    if (messages.length) return messages.join(". ");
  }
  if (detail && typeof detail === "object" && typeof detail.msg === "string")
    return detail.msg;
  return fallback;
}

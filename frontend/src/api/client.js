import axios from "axios";
import { validationMessage } from "./errors.js";
import { resolveApiBase } from "./config.js";

export const api = axios.create({
  baseURL: resolveApiBase(import.meta.env.VITE_API_URL, window.location),
  timeout: 25000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("talentsync_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config ?? {};
    const status = error.response?.status;
    const method = String(config.method ?? "get").toLowerCase();
    const retryable =
      method === "get" &&
      !config.__talentsyncRetried &&
      !config.__skipRetry &&
      (!error.response || [502, 503, 504].includes(status));

    if (retryable) {
      config.__talentsyncRetried = true;
      return api(config);
    }

    const token = localStorage.getItem("talentsync_token");
    const isLogin = /\/auth\/(?:admin\/)?login$/.test(config.url ?? "");
    if (status === 401 && token && !isLogin) {
      localStorage.removeItem("talentsync_token");
      window.dispatchEvent(new CustomEvent("talentsync:session-expired"));
    }
    return Promise.reject(error);
  },
);

export function getApiErrorMessage(
  error,
  fallback = "Ocurrió un error inesperado",
) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map(validationMessage)
      .filter(Boolean);
    if (messages.length) return messages.join(". ");
  }
  if (detail && typeof detail === "object" && typeof detail.msg === "string")
    return detail.msg;
  if (detail && typeof detail === "object" && typeof detail.message === "string")
    return detail.message;
  return fallback;
}

export function apiFileUrl(path) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  const apiBase = new URL(api.defaults.baseURL, window.location.origin);
  return new URL(path, apiBase.origin).toString();
}

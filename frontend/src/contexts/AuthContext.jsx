import { createContext, useEffect, useMemo, useState } from "react";

import { api } from "../api/client.js";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState("");
  const [accessOptions, setAccessOptions] = useState({ mode: "session", providers: [], local_mail: false });

  async function loadUser({ background = false } = {}) {
    if (!background) setLoading(true);
    setAuthError("");
    try {
      const { data } = await api.get("/auth/me", {
        timeout: 8000,
        __skipRetry: true,
        __skipSessionEvent: true,
      });
      setUser(data);
      sessionStorage.setItem("talentsync_last_session_check", String(Date.now()));
    } catch (error) {
      if (error.response?.status === 401) {
        localStorage.removeItem("talentsync_token");
        setUser(null);
      } else if (!background) {
        setAuthError(
          "No pudimos validar tu sesión. Revisa tu conexión y vuelve a intentarlo.",
        );
      }
    } finally {
      if (!background) setLoading(false);
    }
  }

  async function retryAuth() {
    setLoading(true);
    try {
      const { data } = await api.get("/auth/options", { __skipSessionEvent: true });
      setAccessOptions(data);
      await loadUser();
    } catch {
      setAuthError("El servicio de acceso no está disponible. Intenta de nuevo.");
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    async function initialize() {
      try {
        const { data } = await api.get("/auth/options", { __skipSessionEvent: true });
        if (!active) return;
        setAccessOptions(data);
        if (data.mode === "session") localStorage.removeItem("talentsync_token");
      } catch {
        if (!active) return;
        setAuthError("El servicio de acceso no está disponible. Intenta de nuevo.");
        setLoading(false);
        return;
      }
      await loadUser();
    }
    initialize();
    const expireSession = () => {
      setUser(null);
      setLoading(false);
      setAuthError("Tu sesión venció. Ingresa de nuevo para continuar.");
    };
    const validateAfterIdle = () => {
      if (document.visibilityState !== "visible") return;
      const lastCheck = Number(
        sessionStorage.getItem("talentsync_last_session_check") || 0,
      );
      if (Date.now() - lastCheck > 5 * 60 * 1000) loadUser({ background: true });
    };
    window.addEventListener("talentsync:session-expired", expireSession);
    document.addEventListener("visibilitychange", validateAfterIdle);
    return () => {
      active = false;
      window.removeEventListener("talentsync:session-expired", expireSession);
      document.removeEventListener("visibilitychange", validateAfterIdle);
    };
  }, []); // La validación inicial solo debe ejecutarse al montar la aplicación.

  async function login(email, password, options = {}) {
    const suffix = options.admin ? "admin/login" : `${options.portal || "candidate"}/login`;
    if (accessOptions.mode === "legacy") {
      const { data } = await api.post(`/auth/${suffix}`, { email, password, portal: options.portal });
      localStorage.setItem("talentsync_token", data.access_token);
    } else {
      const { data } = await api.post(`/auth/session/${suffix}`, { email, password, code: options.code || null, remember: Boolean(options.remember) });
      if (data.mfa_required) return data;
      localStorage.removeItem("talentsync_token");
    }
    const me = await api.get("/auth/me");
    setUser(me.data);
    setAuthError("");
    localStorage.setItem("talentsync_last_method", "email");
    return me.data;
  }

  async function register(payload) {
    await api.post(`/auth/${payload.role}/register`, payload);
    return login(payload.email, payload.password, { portal: payload.role });
  }

  async function refreshUser() {
    const { data } = await api.get("/auth/me");
    setUser(data);
    return data;
  }

  async function logout() {
    if (accessOptions.mode !== "legacy") await api.post("/auth/session/logout");
    localStorage.removeItem("talentsync_token");
    setUser(null);
    setAuthError("");
  }

  const value = useMemo(
    () => ({ user, loading, authError, accessOptions, login, register, logout, refreshUser, retryAuth }),
    [user, loading, authError, accessOptions],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

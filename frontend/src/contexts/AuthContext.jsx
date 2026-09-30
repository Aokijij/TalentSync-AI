import { createContext, useEffect, useMemo, useState } from "react";

import { api } from "../api/client.js";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState("");

  async function loadUser({ background = false } = {}) {
    const token = localStorage.getItem("talentsync_token");
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    if (!background) setLoading(true);
    setAuthError("");
    try {
      const { data } = await api.get("/auth/me", {
        timeout: 8000,
        __skipRetry: true,
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

  useEffect(() => {
    loadUser();
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
      window.removeEventListener("talentsync:session-expired", expireSession);
      document.removeEventListener("visibilitychange", validateAfterIdle);
    };
  }, []); // La validación inicial solo debe ejecutarse al montar la aplicación.

  async function login(email, password, options = {}) {
    const endpoint = options.admin ? "/auth/admin/login" : "/auth/login";
    const { data } = await api.post(endpoint, { email, password });
    localStorage.setItem("talentsync_token", data.access_token);
    const me = await api.get("/auth/me");
    setUser(me.data);
    setAuthError("");
    return me.data;
  }

  async function register(payload) {
    await api.post("/auth/register", payload);
    return login(payload.email, payload.password);
  }

  async function refreshUser() {
    const { data } = await api.get("/auth/me");
    setUser(data);
    return data;
  }

  function logout() {
    localStorage.removeItem("talentsync_token");
    setUser(null);
    setAuthError("");
  }

  const value = useMemo(
    () => ({ user, loading, authError, login, register, logout, refreshUser, retryAuth: loadUser }),
    [user, loading, authError],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

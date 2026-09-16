import { createContext, useEffect, useMemo, useState } from "react";

import { api } from "../api/client.js";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      const token = localStorage.getItem("talentsync_token");
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const { data } = await api.get("/auth/me");
        setUser(data);
      } catch {
        localStorage.removeItem("talentsync_token");
      } finally {
        setLoading(false);
      }
    }
    loadUser();
  }, []);

  async function login(email, password, options = {}) {
    const endpoint = options.admin ? "/auth/admin/login" : "/auth/login";
    const { data } = await api.post(endpoint, { email, password });
    localStorage.setItem("talentsync_token", data.access_token);
    const me = await api.get("/auth/me");
    setUser(me.data);
    return me.data;
  }

  async function register(payload) {
    await api.post("/auth/register", payload);
    return login(payload.email, payload.password);
  }

  function logout() {
    localStorage.removeItem("talentsync_token");
    setUser(null);
  }

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

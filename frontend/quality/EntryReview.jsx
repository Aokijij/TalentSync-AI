import { useState } from "react";
import { MemoryRouter, useLocation, useNavigate } from "react-router-dom";
import { api } from "../src/api/client.js";
import { AuthContext, AuthProvider } from "../src/contexts/AuthContext.jsx";
import { ThemeProvider } from "../src/contexts/ThemeContext.jsx";
import { FeedbackProvider } from "../src/contexts/FeedbackContext.jsx";
import { AppRoutes } from "../src/routes/AppRoutes.jsx";

export function EntryReview({ params }) {
  const role = params.get("signed");
  const [user, setUser] = useState(role ? { id: 101, name: "Persona de revisión", email: "person@example.com", role, email_verified: params.get("email") !== "pending", mfa_enabled: true, registration_pending: params.get("registration") === "pending" } : null);
  async function refreshUser() { const { data } = await api.get("/auth/me"); setUser(data); return data; }
  if (params.get("session") === "real") return <MemoryRouter initialEntries={[params.get("path") || "/login"]}><ThemeProvider><AuthProvider><FeedbackProvider><AppRoutes /><Location /></FeedbackProvider></AuthProvider></ThemeProvider></MemoryRouter>;
  return <MemoryRouter initialEntries={params.get("history") === "1" ? ["/login", params.get("path") || "/"] : [params.get("path") || "/"]}><ThemeProvider><AuthContext.Provider value={{ user, loading: false, accessOptions: { mode: "session", providers: [], company_mfa_required: false, local_mail: false }, logout: async () => setUser(null), login: async () => {}, register: async () => {}, refreshUser, refreshAccessOptions: async () => ({}) }}><FeedbackProvider><AppRoutes /><Location history={params.get("history") === "1"} /></FeedbackProvider></AuthContext.Provider></ThemeProvider></MemoryRouter>;
}
function Location({ history }) { const location = useLocation(), navigate = useNavigate(); return <><output className="sr-only" aria-label="Ruta de revisión">{location.pathname + location.search + location.hash}</output>{history && <button type="button" style={{ position: "fixed", top: 0, right: 0, zIndex: 100 }} onClick={() => navigate(-1)}>Atrás en revisión</button>}</>; }

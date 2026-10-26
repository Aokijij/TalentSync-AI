import { MemoryRouter, useLocation } from "react-router-dom";
import { AuthContext } from "../src/contexts/AuthContext.jsx";
import { ThemeProvider } from "../src/contexts/ThemeContext.jsx";
import { FeedbackProvider } from "../src/contexts/FeedbackContext.jsx";
import { AppRoutes } from "../src/routes/AppRoutes.jsx";

export function EntryReview({ params }) {
  const role = params.get("signed"), user = role ? { id: 101, name: "Persona de revisión", email: "person@example.com", role, email_verified: params.get("email") !== "pending", mfa_enabled: true } : null;
  return <MemoryRouter initialEntries={[params.get("path") || "/"]}><ThemeProvider><AuthContext.Provider value={{ user, loading: false, accessOptions: { mode: "session", providers: [], company_mfa_required: false, local_mail: false }, logout: async () => {}, login: async () => {}, register: async () => {}, refreshUser: async () => user, refreshAccessOptions: async () => ({}) }}><FeedbackProvider><AppRoutes /><Location /></FeedbackProvider></AuthContext.Provider></ThemeProvider></MemoryRouter>;
}
function Location() { const location = useLocation(); return <output className="sr-only" aria-label="Ruta de revisión">{location.pathname + location.search + location.hash}</output>; }

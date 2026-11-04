import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AuthContext } from "../src/contexts/AuthContext.jsx";
import { ThemeProvider } from "../src/contexts/ThemeContext.jsx";
import { LoginPage } from "../src/pages/LoginPage.jsx";
import { RegisterPage } from "../src/pages/RegisterPage.jsx";
import { SocialAccounts } from "../src/components/SocialAccounts.jsx";
import { SecurityEmailPanel } from "../src/components/SecurityEmailPanel.jsx";
import { SocialAccessPage } from "../src/pages/SocialAccessPage.jsx";
import { SocialRegistrationPage } from "../src/pages/SocialRegistrationPage.jsx";

export function AuthAccessReview({ params }) {
  const providers = ["google", "github", "linkedin"].map((id) => ({ id, enabled: params.get("providers") !== "off", reason: "Este acceso todavía no está disponible." }));
  const accessOptions = { providers, mode: "session", local_mail: true, company_mfa_required: true };
  const screen = params.get("auth"), company = params.get("role") === "company";
  const initial = screen === "complete" ? "/completar-cuenta" : screen === "error" ? `/acceso-social?status=${params.get("status") || "failed"}&provider=google&reason=${params.get("reason") || "provider_unavailable"}` : screen === "register" ? `${company ? "/empresa" : ""}/registro` : screen === "accounts" ? "/seguridad" : `${company ? "/empresa" : ""}/login`;
  return <MemoryRouter initialEntries={[initial]}><ThemeProvider><AuthContext.Provider value={{ accessOptions, login: async () => {}, register: async () => {}, ...(screen === "complete" ? { user: { name: "Persona de ejemplo", email: "example@example.test", registration_pending: true }, refreshUser: async () => {}, logout: async () => {} } : {}) }}>
    <Routes>
      <Route path="/login" element={<LoginPage />} /><Route path="/empresa/login" element={<LoginPage />} />
      <Route path="/registro" element={<RegisterPage />} /><Route path="/empresa/registro" element={<RegisterPage />} />
      <Route path="/acceso-social" element={<SocialAccessPage />} />
      <Route path="/completar-cuenta" element={<SocialRegistrationPage />} />
      <Route path="/seguridad" element={<main className="quality-shell role-candidate"><SecurityEmailPanel user={{ email: "person@example.com", email_verified: true }} localMail /><SocialAccounts user={{ mfa_enabled: false }} providers={providers} onSessionsChanged={async () => {}} /></main>} />
    </Routes>
  </AuthContext.Provider></ThemeProvider></MemoryRouter>;
}

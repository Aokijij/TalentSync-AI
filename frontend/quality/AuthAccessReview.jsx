import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AuthContext } from "../src/contexts/AuthContext.jsx";
import { ThemeProvider } from "../src/contexts/ThemeContext.jsx";
import { LoginPage } from "../src/pages/LoginPage.jsx";
import { RegisterPage } from "../src/pages/RegisterPage.jsx";
import { SocialAccounts } from "../src/components/SocialAccounts.jsx";

export function AuthAccessReview({ params }) {
  const providers = ["google", "github", "linkedin"].map((id) => ({ id, enabled: params.get("providers") !== "off", reason: "Este acceso todavía no está disponible." }));
  const accessOptions = { providers, mode: "session", local_mail: false, company_mfa_required: true };
  const screen = params.get("auth"), company = params.get("role") === "company";
  const initial = screen === "register" ? `${company ? "/empresa" : ""}/registro` : screen === "accounts" ? "/seguridad" : `${company ? "/empresa" : ""}/login`;
  return <MemoryRouter initialEntries={[initial]}><ThemeProvider><AuthContext.Provider value={{ accessOptions, login: async () => {}, register: async () => {} }}>
    <Routes>
      <Route path="/login" element={<LoginPage />} /><Route path="/empresa/login" element={<LoginPage />} />
      <Route path="/registro" element={<RegisterPage />} /><Route path="/empresa/registro" element={<RegisterPage />} />
      <Route path="/seguridad" element={<main className="quality-shell role-candidate"><SocialAccounts user={{ mfa_enabled: false }} providers={providers} onSessionsChanged={async () => {}} /></main>} />
    </Routes>
  </AuthContext.Provider></ThemeProvider></MemoryRouter>;
}

import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { ThemeProvider } from "./contexts/ThemeContext.jsx";
import { LandingPage } from "./pages/LandingPage.jsx";
import { LegalPage } from "./pages/LegalPage.jsx";
import "./styles/index.css";

// Informational release: no authentication provider, API client or account flows.
createRoot(document.getElementById("root")).render(<React.StrictMode><BrowserRouter><ThemeProvider><Routes>
  <Route path="/" element={<LandingPage informational />} />
  <Route path="/candidatos" element={<LandingPage informational />} />
  <Route path="/empresas" element={<LandingPage informational role="company" />} />
  <Route path="/privacidad" element={<LegalPage />} />
  <Route path="/terminos" element={<LegalPage kind="terms" />} />
  <Route path="*" element={<main className="public-container legal-main"><p className="section-kicker">TALENTSYNC</p><h1 className="text-2xl font-bold my-4">El acceso a cuentas está en preparación</h1><p>Consulta las funcionalidades y la información de privacidad desde el sitio público.</p><Link className="button-primary mt-6" to="/">Ir al inicio</Link></main>} />
</Routes></ThemeProvider></BrowserRouter></React.StrictMode>);

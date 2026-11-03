import { renderToString } from "react-dom/server";
import { StaticRouter } from "react-router-dom";
import { LandingPage } from "./pages/LandingPage.jsx";
import { LegalPage } from "./pages/LegalPage.jsx";
import { ThemeContext } from "./contexts/ThemeContext.jsx";

export function renderPublicPage(path, informational = true) {
  return renderToString(<StaticRouter location={path}><ThemeContext.Provider value={{ theme: "light", toggleTheme: () => {} }}>
    {["/", "/candidatos", "/empresas"].includes(path) ? <LandingPage informational={informational} role={path === "/empresas" ? "company" : "candidate"} /> : <LegalPage kind={path === "/terminos" ? "terms" : "privacy"} />}
  </ThemeContext.Provider></StaticRouter>);
}

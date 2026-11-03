import React, { useLayoutEffect } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { AuthProvider } from "./contexts/AuthContext.jsx";
import { AppRoutes } from "./routes/AppRoutes.jsx";
import { ThemeProvider } from "./contexts/ThemeContext.jsx";
import { FeedbackProvider } from "./contexts/FeedbackContext.jsx";
import "./styles/index.css";
import "./styles/review-refinements.css";
import "./styles/catalog-organization.css";
import { loadAppFont } from "./utils/fontLoading.js";

loadAppFont(document);

function StartupBoundary({ children }) {
  useLayoutEffect(() => { document.documentElement.removeAttribute("data-app-route"); document.title = "TalentSync"; }, []);
  return children;
}

createRoot(document.getElementById("root")).render(
  <React.StrictMode><StartupBoundary>
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <FeedbackProvider><AppRoutes /></FeedbackProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  </StartupBoundary></React.StrictMode>,
);

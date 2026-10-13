import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { AuthProvider } from "./contexts/AuthContext.jsx";
import { AppRoutes } from "./routes/AppRoutes.jsx";
import { ThemeProvider } from "./contexts/ThemeContext.jsx";
import { FeedbackProvider } from "./contexts/FeedbackContext.jsx";
import "./styles/index.css";
import "./styles/review-refinements.css";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <FeedbackProvider><AppRoutes /></FeedbackProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>,
);

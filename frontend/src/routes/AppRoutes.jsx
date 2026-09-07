import { Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "../hooks/useAuth.js";
import { AppLayout } from "../layouts/AppLayout.jsx";
import { AdminDashboard } from "../pages/AdminDashboard.jsx";
import { AdminManagementPage } from "../pages/AdminManagementPage.jsx";
import { CandidateDashboard } from "../pages/CandidateDashboard.jsx";
import { CandidateDetailPage } from "../pages/CandidateDetailPage.jsx";
import { CompanyDashboard } from "../pages/CompanyDashboard.jsx";
import { CompanyApplicationsPage } from "../pages/CompanyApplicationsPage.jsx";
import { CompanyJobsPage } from "../pages/CompanyJobsPage.jsx";
import { CompanySettingsPage } from "../pages/CompanySettingsPage.jsx";
import { CompanyTalentPage } from "../pages/CompanyTalentPage.jsx";
import { CompanyCandidatesPage } from "../pages/CompanyCandidatesPage.jsx";
import { JobsPage } from "../pages/JobsPage.jsx";
import { JobDetailPage } from "../pages/JobDetailPage.jsx";
import { LoginPage } from "../pages/LoginPage.jsx";
import { ApplicationsPage } from "../pages/ApplicationsPage.jsx";
import { ProfilePage } from "../pages/ProfilePage.jsx";
import { RecommendationsPage } from "../pages/RecommendationsPage.jsx";
import { NotificationsPage } from "../pages/NotificationsPage.jsx";
import { RegisterPage } from "../pages/RegisterPage.jsx";

function RequireAuth({ children }) {
  const { user, loading } = useAuth();

  if (loading)
    return (
      <div className="grid min-h-screen place-items-center text-steel">
        Cargando...
      </div>
    );
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function HomeRedirect() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "company") return <Navigate to="/empresa" replace />;
  if (user.role === "admin") return <Navigate to="/admin" replace />;
  return <Navigate to="/candidato" replace />;
}

function RequireRole({ roles, children }) {
  const { user } = useAuth();
  return roles.includes(user.role) ? children : <HomeRedirect />;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/registro" element={<RegisterPage />} />
      <Route path="/" element={<HomeRedirect />} />

      <Route
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route
          path="/candidato"
          element={
            <RequireRole roles={["candidate"]}>
              <CandidateDashboard />
            </RequireRole>
          }
        />
        <Route
          path="/empresa"
          element={
            <RequireRole roles={["company"]}>
              <CompanyDashboard />
            </RequireRole>
          }
        />
        <Route
          path="/empresa/vacantes"
          element={
            <RequireRole roles={["company"]}>
              <CompanyJobsPage />
            </RequireRole>
          }
        />
        <Route
          path="/empresa/talento"
          element={
            <RequireRole roles={["company"]}>
              <CompanyTalentPage />
            </RequireRole>
          }
        />
        <Route
          path="/empresa/postulaciones"
          element={
            <RequireRole roles={["company"]}>
              <CompanyApplicationsPage />
            </RequireRole>
          }
        />
        <Route
          path="/empresa/perfil"
          element={
            <RequireRole roles={["company"]}>
              <CompanySettingsPage />
            </RequireRole>
          }
        />
        <Route
          path="/admin"
          element={
            <RequireRole roles={["admin"]}>
              <AdminDashboard />
            </RequireRole>
          }
        />
        <Route
          path="/administracion"
          element={
            <RequireRole roles={["admin"]}>
              <AdminManagementPage />
            </RequireRole>
          }
        />
        <Route
          path="/vacantes"
          element={
            <RequireRole roles={["candidate", "admin"]}>
              <JobsPage />
            </RequireRole>
          }
        />
        <Route path="/vacantes/:jobId" element={<JobDetailPage />} />
        <Route
          path="/recomendaciones"
          element={
            <RequireRole roles={["candidate"]}>
              <RecommendationsPage />
            </RequireRole>
          }
        />
        <Route
          path="/postulaciones"
          element={
            <RequireRole roles={["candidate"]}>
              <ApplicationsPage />
            </RequireRole>
          }
        />
        <Route
          path="/notificaciones"
          element={
            <RequireRole roles={["candidate", "company"]}>
              <NotificationsPage />
            </RequireRole>
          }
        />
        <Route
          path="/empresa/vacantes/:jobId/candidatos"
          element={
            <RequireRole roles={["company"]}>
              <CompanyCandidatesPage />
            </RequireRole>
          }
        />
        <Route
          path="/empresa/candidatos/:userId"
          element={
            <RequireRole roles={["company"]}>
              <CandidateDetailPage />
            </RequireRole>
          }
        />
        <Route
          path="/perfil"
          element={
            <RequireRole roles={["candidate"]}>
              <ProfilePage />
            </RequireRole>
          }
        />
      </Route>
    </Routes>
  );
}

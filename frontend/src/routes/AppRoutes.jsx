import { lazy, Suspense } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import { useAuth } from "../hooks/useAuth.js";
import { AppLayout } from "../layouts/AppLayout.jsx";

const lazyNamed = (loader, name) =>
  lazy(() => loader().then((module) => ({ default: module[name] })));

const AdminDashboard = lazyNamed(() => import("../pages/AdminDashboard.jsx"), "AdminDashboard");
const AdminLoginPage = lazyNamed(() => import("../pages/AdminLoginPage.jsx"), "AdminLoginPage");
const AdminManagementPage = lazyNamed(() => import("../pages/AdminManagementPage.jsx"), "AdminManagementPage");
const ApplicationsPage = lazyNamed(() => import("../pages/ApplicationsPage.jsx"), "ApplicationsPage");
const CandidateDashboard = lazyNamed(() => import("../pages/CandidateDashboard.jsx"), "CandidateDashboard");
const CandidateDetailPage = lazyNamed(() => import("../pages/CandidateDetailPage.jsx"), "CandidateDetailPage");
const CompanyApplicationsPage = lazyNamed(() => import("../pages/CompanyApplicationsPage.jsx"), "CompanyApplicationsPage");
const CompanyCandidatesPage = lazyNamed(() => import("../pages/CompanyCandidatesPage.jsx"), "CompanyCandidatesPage");
const CompanyDashboard = lazyNamed(() => import("../pages/CompanyDashboard.jsx"), "CompanyDashboard");
const CompanyJobsPage = lazyNamed(() => import("../pages/CompanyJobsPage.jsx"), "CompanyJobsPage");
const CompanyProfilePage = lazyNamed(() => import("../pages/CompanyProfilePage.jsx"), "CompanyProfilePage");
const CompanySettingsPage = lazyNamed(() => import("../pages/CompanySettingsPage.jsx"), "CompanySettingsPage");
const CompanyTalentPage = lazyNamed(() => import("../pages/CompanyTalentPage.jsx"), "CompanyTalentPage");
const JobDetailPage = lazyNamed(() => import("../pages/JobDetailPage.jsx"), "JobDetailPage");
const JobsPage = lazyNamed(() => import("../pages/JobsPage.jsx"), "JobsPage");
const LoginPage = lazyNamed(() => import("../pages/LoginPage.jsx"), "LoginPage");
const NotificationsPage = lazyNamed(() => import("../pages/NotificationsPage.jsx"), "NotificationsPage");
const ProfilePage = lazyNamed(() => import("../pages/ProfilePage.jsx"), "ProfilePage");
const RecommendationsPage = lazyNamed(() => import("../pages/RecommendationsPage.jsx"), "RecommendationsPage");
const RegisterPage = lazyNamed(() => import("../pages/RegisterPage.jsx"), "RegisterPage");

function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading)
    return (
      <div className="grid min-h-screen place-items-center text-steel">
        Cargando...
      </div>
    );
  if (!user) {
    const adminArea = ["/admin", "/administracion"].some((path) =>
      location.pathname.startsWith(path),
    );
    return <Navigate to={adminArea ? "/acceso-administracion" : "/login"} replace />;
  }
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
    <Suspense fallback={<div className="grid min-h-screen place-items-center text-[var(--muted)]">Cargando sección...</div>}>
      <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/acceso-administracion" element={<AdminLoginPage />} />
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
          path="/empresas/:companyId"
          element={
            <RequireRole roles={["candidate", "admin"]}>
              <CompanyProfilePage />
            </RequireRole>
          }
        />
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
    </Suspense>
  );
}

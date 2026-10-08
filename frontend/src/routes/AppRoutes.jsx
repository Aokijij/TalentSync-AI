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
const SocialAccessPage = lazyNamed(() => import("../pages/SocialAccessPage.jsx"), "SocialAccessPage");
const NotificationsPage = lazyNamed(() => import("../pages/NotificationsPage.jsx"), "NotificationsPage");
const ProfilePage = lazyNamed(() => import("../pages/ProfilePage.jsx"), "ProfilePage");
const RecommendationsPage = lazyNamed(() => import("../pages/RecommendationsPage.jsx"), "RecommendationsPage");
const RegisterPage = lazyNamed(() => import("../pages/RegisterPage.jsx"), "RegisterPage");
const SecurityPage = lazyNamed(() => import("../pages/SecurityPage.jsx"), "SecurityPage");
const AccountActionPage = lazyNamed(() => import("../pages/AccountActionPage.jsx"), "AccountActionPage");
const LocalMailboxPage = lazyNamed(() => import("../pages/LocalMailboxPage.jsx"), "LocalMailboxPage");
const OnboardingPage = lazyNamed(() => import("../pages/OnboardingPage.jsx"), "OnboardingPage");
const OrganizationPage = lazyNamed(() => import("../pages/OrganizationPage.jsx"), "OrganizationPage");
const VerificationQueuePage = lazyNamed(() => import("../pages/OrganizationPage.jsx"), "VerificationQueuePage");
const InvitationPage = lazyNamed(() => import("../pages/OrganizationPage.jsx"), "InvitationPage");
const CompatibilityPage = lazyNamed(() => import("../pages/CompatibilityPage.jsx"), "CompatibilityPage");
const ProcessPage = lazyNamed(() => import("../pages/ProcessPage.jsx"), "ProcessPage");
const InterviewsPage = lazyNamed(() => import("../pages/InterviewPage.jsx"), "InterviewsPage");
const InterviewRoomPage = lazyNamed(() => import("../pages/InterviewPage.jsx"), "InterviewRoomPage");
const LearningPage = lazyNamed(() => import("../pages/LearningPage.jsx"), "LearningPage");
const LearningCatalogPage = lazyNamed(() => import("../pages/LearningCatalogPage.jsx"), "LearningCatalogPage");
const HiringQualityPage = lazyNamed(() => import("../pages/HiringQualityPage.jsx"), "HiringQualityPage");
const TrustPage = lazyNamed(() => import("../pages/EcosystemPage.jsx"), "TrustPage");
const EcosystemPage = lazyNamed(() => import("../pages/EcosystemPage.jsx"), "EcosystemPage");
const ModelPage = lazyNamed(() => import("../pages/ModelPage.jsx"), "ModelPage");
const PersonalizationPage = lazyNamed(() => import("../pages/ModelPage.jsx"), "PersonalizationPage");

function RequireAuth({ children }) {
  const { user, loading, authError, retryAuth, logout, accessOptions } = useAuth();
  const location = useLocation();

  if (loading)
    return (
      <div className="grid min-h-screen place-items-center text-steel">
        <div className="text-center">
          <div className="mx-auto h-9 w-9 animate-spin rounded-full border-2 border-[var(--line)] border-t-[var(--accent)]" />
          <p className="mt-3">Validando tu sesión...</p>
        </div>
      </div>
    );
  if (authError)
    return (
      <div className="grid min-h-screen place-items-center bg-[var(--canvas)] px-5">
        <section className="surface-card max-w-md p-7 text-center">
          <h1 className="text-xl font-bold text-[var(--ink)]">No pudimos cargar tu espacio</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">{authError}</p>
          <div className="mt-5 flex justify-center gap-3">
            <button className="button-primary" type="button" onClick={() => retryAuth()}>Reintentar</button>
            <button className="button-secondary" type="button" onClick={logout}>Cerrar sesión</button>
          </div>
        </section>
      </div>
    );
  if (!user) {
    const adminArea = ["/admin", "/administracion"].some((path) =>
      location.pathname.startsWith(path),
    );
    return <Navigate to={adminArea ? "/acceso-administracion" : "/login"} state={{ from: location.pathname + location.search }} replace />;
  }
  if (accessOptions.mode === "session" && user.role !== "candidate" && !user.mfa_enabled && location.pathname !== "/seguridad") return <Navigate to="/seguridad" replace />;
  return children;
}

function HomeRedirect() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "company") return <Navigate to="/empresa/equipo" replace />;
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
      <Route path="/acceso-social" element={<SocialAccessPage />} />
      <Route path="/acceso-administracion" element={<AdminLoginPage />} />
      <Route path="/acceso-corporativo" element={<SocialAccessPage administrative />} />
      <Route path="/registro" element={<RegisterPage />} />
      <Route path="/empresa/login" element={<LoginPage />} />
      <Route path="/empresa/registro" element={<RegisterPage />} />
      <Route path="/recuperar-acceso" element={<AccountActionPage recover />} />
      <Route path="/cuenta/confirmar" element={<AccountActionPage />} />
      <Route path="/desarrollo/correos" element={<LocalMailboxPage />} />
      <Route path="/equipo/invitacion" element={<InvitationPage />} />
      <Route path="/" element={<HomeRedirect />} />

      <Route
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route path="/seguridad" element={<SecurityPage />} />
        <Route path="/confianza" element={<RequireRole roles={["candidate", "company"]}><TrustPage /></RequireRole>} />
        <Route path="/admin/ecosistema" element={<RequireRole roles={["admin"]}><EcosystemPage /></RequireRole>} />
        <Route path="/admin/modelos" element={<RequireRole roles={["admin"]}><ModelPage /></RequireRole>} />
        <Route path="/admin/aprendizaje" element={<RequireRole roles={["admin"]}><LearningCatalogPage /></RequireRole>} />
        <Route path="/mis-intereses" element={<RequireRole roles={["candidate"]}><PersonalizationPage /></RequireRole>} />
        <Route path="/empresa/calidad" element={<RequireRole roles={["company"]}><HiringQualityPage /></RequireRole>} />
        <Route path="/aprendizaje" element={<RequireRole roles={["candidate"]}><LearningPage /></RequireRole>} />
        <Route path="/procesos/:applicationId" element={<ProcessPage />} />
        <Route path="/entrevistas" element={<InterviewsPage />} />
        <Route path="/entrevistas/:roomId" element={<InterviewRoomPage />} />
        <Route path="/compatibilidad" element={<RequireRole roles={["candidate", "company"]}><CompatibilityPage /></RequireRole>} />
        <Route path="/empresa/equipo" element={<RequireRole roles={["company"]}><OrganizationPage /></RequireRole>} />
        <Route path="/admin/verificaciones" element={<RequireRole roles={["admin"]}><VerificationQueuePage /></RequireRole>} />
        <Route path="/bienvenida" element={<RequireRole roles={["candidate"]}><OnboardingPage /></RequireRole>} />
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

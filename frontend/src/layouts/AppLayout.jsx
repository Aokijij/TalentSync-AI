import { CompanyAccessNotice } from "../components/CompanyAccessNotice.jsx";
import { useEffect, useRef, useState } from "react";
import { LogOut, Menu, X } from "lucide-react";
import { navigationLinks as links } from "../constants/navigation.js";
import "../styles/navigation.css";
import { Navigate, NavLink, Outlet, useLocation } from "react-router-dom";

import { api } from "../api/client.js";
import { BrandLogo } from "../components/brand/BrandLogo.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { ThemeToggle } from "../components/ThemeToggle.jsx";


const roleCopy = {
  candidate: {
    label: "Candidato",
    caption: "Oportunidades guiadas por evidencia",
  },
  company: { label: "Empresa", caption: "Selección basada en señales reales" },
  admin: { label: "Administrador", caption: "Operación y salud de plataforma" },
};

const navigationOrder = ["/candidato", "/empresa", "/admin", "/recomendaciones", "/vacantes", "/empresa/vacantes", "/postulaciones", "/empresa/postulaciones", "/empresa/talento", "/compatibilidad", "/aprendizaje", "/entrevistas", "/mis-intereses", "/empresa/calidad", "/confianza", "/admin/verificaciones", "/admin/ecosistema", "/admin/modelos", "/admin/aprendizaje", "/perfil", "/empresa/perfil", "/empresa/equipo", "/administracion", "/notificaciones", "/seguridad"];

function Navigation({ linksForRole, unreadNotifications, onNavigate, role }) {
  const Container = role ? "nav" : "div";
  const groups = role === "company" ? [["Contratación", ["/empresa", "/empresa/vacantes", "/empresa/postulaciones", "/empresa/talento", "/empresa/calidad"]], ["Organización", ["/empresa/perfil", "/empresa/equipo", "/confianza"]], ["Tu cuenta", ["/notificaciones", "/seguridad", "/guia"]]] : role === "admin" ? [["Supervisión", ["/admin", "/admin/verificaciones", "/admin/ecosistema", "/vacantes"]], ["Plataforma", ["/admin/modelos", "/admin/aprendizaje", "/administracion"]], ["Tu cuenta", ["/seguridad", "/guia"]]] : [["Oportunidades", ["/candidato", "/recomendaciones", "/vacantes", "/postulaciones"]], ["Tu trayectoria", ["/aprendizaje", "/perfil"]], ["Tu cuenta", ["/notificaciones", "/confianza", "/seguridad", "/guia"]]];
  return (
    <Container className="space-y-1" aria-label={role ? "Navegación principal" : undefined}>
      {role ? groups.map(([label, routes]) => { const group = routes.map((to) => linksForRole.find((link) => link.to === to)).filter(Boolean); return group.length ? <div key={label} className="navigation-group app-nav-group"><p className="mb-2 px-3 text-[10px] font-bold uppercase tracking-widest text-[var(--sidebar-muted)]">{label}</p><Navigation linksForRole={group} unreadNotifications={unreadNotifications} onNavigate={onNavigate} /></div> : null; }) : linksForRole.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          end={["/candidato", "/empresa", "/admin"].includes(to)}
          onClick={onNavigate}
          className={({ isActive }) =>
            `app-nav-link focus-ring ${isActive ? "is-active" : ""}`
          }
        >
          {() => (
            <>
              <span className="app-nav-icon"><Icon size={19} strokeWidth={1.9} aria-hidden="true" /></span>
              <span className="app-nav-label">{label}</span>
              {to === "/notificaciones" && unreadNotifications > 0 ? (
                <span
                  className="app-nav-count"
                >
                  {unreadNotifications > 99 ? "99+" : unreadNotifications}
                </span>
              ) : null}
            </>
          )}
        </NavLink>
      ))}
    </Container>
  );
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  useEffect(() => {
    document.documentElement.dataset.role = user.role;
    return () => { delete document.documentElement.dataset.role; };
  }, [user.role]);
  useEffect(() => { window.scrollTo({ top: 0, left: 0, behavior: "instant" }); }, [location.pathname]);
  const [unreadNotifications, setUnreadNotifications] = useState(0);
  const [organizationName, setOrganizationName] = useState("");
  const [organization, setOrganization] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuDialog = useRef(null), menuTrigger = useRef(null);
  useEffect(() => {
    if (!menuOpen) return;
    const media = window.matchMedia("(min-width:1024px)");
    if (media.matches) { setMenuOpen(false); return; }
    const node = menuDialog.current, overflow = document.body.style.overflow;
    node.showModal(); document.body.style.overflow = "hidden";
    const focus = requestAnimationFrame(() => node.querySelector(".app-mobile-close")?.focus());
    const resize = () => { if (media.matches) setMenuOpen(false); };
    media.addEventListener("change", resize);
    return () => { cancelAnimationFrame(focus); media.removeEventListener("change", resize); node.close(); document.body.style.overflow = overflow; if (menuTrigger.current?.isConnected) menuTrigger.current.focus(); };
  }, [menuOpen]);
  const copy = roleCopy[user.role] ?? roleCopy.candidate;
  const visibleLinks = links.filter((link) => link.roles.includes(user.role) && (organization?.active !== false || ["/empresa/equipo", "/seguridad"].includes(link.to)) && (organization?.role !== "interviewer" || ["/seguridad", "/empresa/equipo", "/notificaciones", "/guia"].includes(link.to)) && (organization?.role !== "recruiter" || link.to !== "/empresa/perfil"))
    .map((link) => organization?.role === "interviewer" && link.to === "/empresa/equipo" ? { ...link, label: "Mis entrevistas" } : link)
    .sort((left, right) => navigationOrder.indexOf(left.to) - navigationOrder.indexOf(right.to));

  useEffect(() => {
    if (user.role !== "candidate" && user.role !== "company") return;
    let active = true;
    const refreshCount = () => {
      if (document.hidden) return;
      api.get("/notifications/unread-count", { __quiet: true })
        .then(({ data }) => { if (active) setUnreadNotifications(data.count || 0); })
        .catch(() => {});
    };
    const handleChange = (event) =>
      event.detail?.count != null
        ? setUnreadNotifications(event.detail.count)
        : refreshCount();
    refreshCount();
    window.addEventListener("talentsync:notifications-changed", handleChange);
    window.addEventListener("focus", refreshCount);
    document.addEventListener("visibilitychange", refreshCount);
    const timer = setInterval(refreshCount, 30000);
    return () => {
      active = false; clearInterval(timer);
      window.removeEventListener("talentsync:notifications-changed", handleChange);
      window.removeEventListener("focus", refreshCount);
      document.removeEventListener("visibilitychange", refreshCount);
    };
  }, [user.role]);

  useEffect(() => {
    if (user.role !== "company") {
      setOrganizationName("");
      return;
    }
    let current = true;
    api.get("/organization/access").then(async ({ data: access }) => {
      const data = access.active === false ? access : { ...access, ...(await api.get("/organization/me")).data };
      if (current) { setOrganizationName(data.company_name || data.name || ""); setOrganization(data); }
    }).catch(() => { if (current) setOrganizationName(""); });
    return () => { current = false; };
  }, [user.id, user.role, location.pathname]);

  const closeMenu = () => setMenuOpen(false);
  function keepMenuFocus(event) {
    if (event.key !== "Tab") return;
    const items = [...event.currentTarget.querySelectorAll('a[href],button:not(:disabled),[tabindex="0"]')].filter((node) => node.getClientRects().length);
    const first = items[0], last = items.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
  }
  if (organization?.role === "interviewer" && !["/empresa/equipo", "/notificaciones", "/seguridad", "/guia"].includes(location.pathname) && !location.pathname.startsWith("/procesos/")) return <Navigate to="/empresa/equipo" replace />;

  return (
    <div
      className={`role-${user.role} min-h-screen bg-[var(--canvas)] text-[var(--ink-strong)]`}
    >
      <a className="app-skip-link" href="#main-content">Saltar al contenido</a>
      <aside className="app-sidebar fixed inset-y-0 left-0 z-30 hidden w-72 flex-col overflow-y-auto border-r border-[var(--sidebar-border)] px-4 py-5 lg:flex">
        <Brand copy={copy} user={user} displayName={organizationName} />
        <div className="mt-8">
          <Navigation
            role={user.role}
            linksForRole={visibleLinks}
            unreadNotifications={unreadNotifications}
          />
        </div>
        <SidebarFooter logout={logout} />
      </aside>

      <header className="app-mobile-header sticky top-0 z-20 flex min-h-16 items-center justify-between border-b border-[var(--line)] bg-[var(--canvas)]/95 px-4 backdrop-blur lg:hidden">
        <BrandLogo size="sm" subtitle={copy.label} />
        <div className="flex gap-2">
          <ThemeToggle compact />
          <button
            type="button"
            ref={menuTrigger}
            className="button-secondary !min-h-11 !w-11 !p-0"
            aria-label={menuOpen ? "Cerrar menú" : "Abrir menú"}
            aria-expanded={menuOpen}
            aria-controls="app-mobile-navigation"
            aria-haspopup="dialog"
            onClick={() => setMenuOpen((open) => !open)}
          >
            {menuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </header>

      {menuOpen ? (
        <dialog ref={menuDialog} id="app-mobile-navigation" aria-label="Navegación principal" className="app-mobile-navigation" onKeyDown={keepMenuFocus} onCancel={(event) => { event.preventDefault(); closeMenu(); }} onClick={(event) => { if (event.target === event.currentTarget) closeMenu(); }}>
          <aside className="app-sidebar relative flex h-full w-[min(19rem,86vw)] flex-col overflow-y-auto p-4">
            <button type="button" className="app-mobile-close" aria-label="Cerrar menú" onClick={closeMenu}><X size={19} /></button>
            <Brand copy={copy} user={user} displayName={organizationName} />
            <div className="mt-8">
              <Navigation
                role={user.role}
            linksForRole={visibleLinks}
                unreadNotifications={unreadNotifications}
                onNavigate={closeMenu}
              />
            </div>
            <SidebarFooter logout={logout} />
          </aside>
        </dialog>
      ) : null}

      <main id="main-content" tabIndex={-1} className="lg:pl-72">
        {user.role === "company" && <header className="business-workspace-header flex flex-wrap items-center justify-between gap-3 border-b border-[var(--line)] bg-[var(--surface)] px-6 py-4"><div><p className="text-[10px] font-bold uppercase tracking-widest text-[var(--muted)]">Centro de contratación</p><p className="mt-1 font-bold">{organizationName || "Mi organización"}</p></div><div className="flex items-center gap-3 text-xs"><span className="rounded-full border border-[var(--line)] px-3 py-2">{organization?.active === false ? "Acceso retirado" : organization?.verification_status === "suspended" ? "Empresa suspendida" : organization?.verification_status === "verified" ? "Empresa verificada" : "Verificación pendiente"}</span><span>{organization?.role === "owner" ? "Propietario" : organization?.role === "interviewer" ? "Entrevistador" : "Reclutador"}</span></div></header>}
        <div className="app-content mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8 lg:px-10">
          {organization?.active === false && location.pathname !== "/seguridad" ? <CompanyAccessNotice access={organization} /> : <>{organization?.verification_status === "suspended" && <div className="mb-5"><CompanyAccessNotice access={organization} /></div>}<Outlet /></>}
        </div>
      </main>
    </div>
  );
}

function Brand({ copy, user, displayName }) {
  return (
    <div>
      <BrandLogo className="px-2" tone="inverse" />
      <div className="app-nav-account mt-7 rounded-xl border border-white/15 bg-black/10 px-3 py-3">
        <p className="truncate text-sm font-bold text-white">
          {displayName || user.name}
        </p>
        <p className="mt-1 text-xs text-[var(--sidebar-muted)]">{copy.label}</p>
      </div>
    </div>
  );
}

function SidebarFooter({ logout }) {
  return (
    <div className="app-sidebar-footer mt-auto space-y-1 pt-6">
      <ThemeToggle className="app-nav-utility" />
      <button
        type="button"
        onClick={logout}
        className="app-nav-utility focus-ring"
      >
        <LogOut size={18} aria-hidden="true" />
        Cerrar sesión
      </button>
    </div>
  );
}

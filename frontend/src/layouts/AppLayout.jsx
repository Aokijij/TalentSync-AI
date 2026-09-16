import { useEffect, useState } from "react";
import {
  Bell,
  BriefcaseBusiness,
  Building2,
  FileCheck2,
  LayoutDashboard,
  LogOut,
  Menu,
  ShieldCheck,
  Sparkles,
  UserRound,
  X,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

import { api } from "../api/client.js";
import { BrandLogo } from "../components/brand/BrandLogo.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { ThemeToggle } from "../components/ThemeToggle.jsx";

const links = [
  { to: "/admin", label: "Inicio", icon: LayoutDashboard, roles: ["admin"] },
  {
    to: "/administracion",
    label: "Gestionar plataforma",
    icon: ShieldCheck,
    roles: ["admin"],
  },
  {
    to: "/candidato",
    label: "Inicio",
    icon: LayoutDashboard,
    roles: ["candidate"],
  },
  {
    to: "/recomendaciones",
    label: "Recomendaciones",
    icon: Sparkles,
    roles: ["candidate"],
  },
  {
    to: "/vacantes",
    label: "Explorar vacantes",
    icon: BriefcaseBusiness,
    roles: ["candidate", "admin"],
  },
  {
    to: "/postulaciones",
    label: "Postulaciones",
    icon: FileCheck2,
    roles: ["candidate"],
  },
  { to: "/perfil", label: "Mi perfil", icon: UserRound, roles: ["candidate"] },
  {
    to: "/notificaciones",
    label: "Notificaciones",
    icon: Bell,
    roles: ["candidate"],
  },
  {
    to: "/empresa",
    label: "Inicio",
    icon: LayoutDashboard,
    roles: ["company"],
  },
  {
    to: "/empresa/vacantes",
    label: "Mis vacantes",
    icon: BriefcaseBusiness,
    roles: ["company"],
  },
  {
    to: "/empresa/talento",
    label: "Buscar talento",
    icon: Sparkles,
    roles: ["company"],
  },
  {
    to: "/empresa/postulaciones",
    label: "Postulaciones",
    icon: FileCheck2,
    roles: ["company"],
  },
  {
    to: "/empresa/perfil",
    label: "Perfil empresa",
    icon: Building2,
    roles: ["company"],
  },
  {
    to: "/notificaciones",
    label: "Notificaciones",
    icon: Bell,
    roles: ["company"],
  },
];

const roleCopy = {
  candidate: {
    label: "Candidato",
    caption: "Oportunidades guiadas por evidencia",
  },
  company: { label: "Empresa", caption: "Selección basada en señales reales" },
  admin: { label: "Administrador", caption: "Operación y salud de plataforma" },
};

function Navigation({ linksForRole, unreadNotifications, onNavigate }) {
  return (
    <nav className="space-y-1" aria-label="Navegación principal">
      {linksForRole.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          end
          onClick={onNavigate}
          className={({ isActive }) =>
            `flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm font-semibold transition-colors focus-ring ${
              isActive
                ? "bg-white text-[var(--sidebar)]"
                : "text-[var(--sidebar-ink)] hover:bg-white/10 hover:text-white"
            }`
          }
        >
          {({ isActive }) => (
            <>
              <Icon
                size={18}
                strokeWidth={isActive ? 2.4 : 1.9}
                aria-hidden="true"
              />
              <span>{label}</span>
              {to === "/notificaciones" && unreadNotifications > 0 ? (
                <span
                  className={`ml-auto rounded-full px-2 py-0.5 text-xs font-bold ${isActive ? "bg-sky-100 text-sky-900" : "bg-sky-400 text-sky-950"}`}
                >
                  {unreadNotifications > 99 ? "99+" : unreadNotifications}
                </span>
              ) : null}
            </>
          )}
        </NavLink>
      ))}
    </nav>
  );
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const [unreadNotifications, setUnreadNotifications] = useState(0);
  const [menuOpen, setMenuOpen] = useState(false);
  const copy = roleCopy[user.role] ?? roleCopy.candidate;
  const visibleLinks = links.filter((link) => link.roles.includes(user.role));

  useEffect(() => {
    if (user.role !== "candidate" && user.role !== "company") return;
    const refreshCount = () =>
      api
        .get("/notifications/unread-count")
        .then(({ data }) => setUnreadNotifications(data.count || 0))
        .catch(() => setUnreadNotifications(0));
    const handleChange = (event) =>
      event.detail?.count != null
        ? setUnreadNotifications(event.detail.count)
        : refreshCount();
    refreshCount();
    window.addEventListener("talentsync:notifications-changed", handleChange);
    return () =>
      window.removeEventListener(
        "talentsync:notifications-changed",
        handleChange,
      );
  }, [user.role]);

  const closeMenu = () => setMenuOpen(false);

  return (
    <div
      className={`role-${user.role} min-h-screen bg-[var(--canvas)] text-[var(--ink-strong)]`}
    >
      <aside className="app-sidebar fixed inset-y-0 left-0 z-30 hidden w-72 flex-col border-r border-[var(--sidebar-border)] px-4 py-5 lg:flex">
        <Brand copy={copy} user={user} />
        <div className="mt-8">
          <Navigation
            linksForRole={visibleLinks}
            unreadNotifications={unreadNotifications}
          />
        </div>
        <SidebarFooter logout={logout} />
      </aside>

      <header className="sticky top-0 z-20 flex min-h-16 items-center justify-between border-b border-[var(--line)] bg-[var(--canvas)]/95 px-4 backdrop-blur lg:hidden">
        <BrandLogo size="sm" subtitle={copy.label} />
        <div className="flex gap-2">
          <ThemeToggle compact />
          <button
            type="button"
            className="button-secondary !min-h-11 !w-11 !p-0"
            aria-label={menuOpen ? "Cerrar menú" : "Abrir menú"}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((open) => !open)}
          >
            {menuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </header>

      {menuOpen ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 cursor-default bg-slate-950/35"
            aria-label="Cerrar menú"
            onClick={closeMenu}
          />
          <aside className="app-sidebar relative flex h-full w-[min(19rem,86vw)] flex-col p-4">
            <Brand copy={copy} user={user} />
            <div className="mt-8">
              <Navigation
                linksForRole={visibleLinks}
                unreadNotifications={unreadNotifications}
                onNavigate={closeMenu}
              />
            </div>
            <SidebarFooter logout={logout} />
          </aside>
        </div>
      ) : null}

      <main className="lg:pl-72">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8 lg:px-10">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

function Brand({ copy, user }) {
  return (
    <div>
      <BrandLogo className="px-2" tone="inverse" />
      <div className="mt-7 rounded-xl border border-white/15 bg-black/10 px-3 py-3">
        <p className="truncate text-sm font-bold text-white">{user.name}</p>
        <p className="mt-1 text-xs text-[var(--sidebar-muted)]">{copy.label}</p>
      </div>
    </div>
  );
}

function SidebarFooter({ logout }) {
  return (
    <div className="mt-auto space-y-1 pt-6">
      <ThemeToggle />
      <button
        type="button"
        onClick={logout}
        className="flex min-h-11 w-full items-center gap-3 rounded-xl px-3 text-sm font-semibold text-[var(--sidebar-ink)] transition-colors hover:bg-white/10 hover:text-white focus-ring"
      >
        <LogOut size={18} aria-hidden="true" />
        Cerrar sesión
      </button>
    </div>
  );
}

import { Component } from "react";
import { useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";
import { accountHome } from "../utils/accountAccess.js";

class RecoveryBoundary extends Component {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(error) {
    const chunkFailure = /dynamically imported module|loading chunk|importing a module script|failed to fetch.*module/i.test(String(error?.message));
    const safeEntry = /^(?:\/login|\/empresa\/login|\/completar-cuenta|\/empresa\/bienvenida)$/.test(this.props.path);
    if (chunkFailure && safeEntry) {
      try {
        const key = `talentsync:entry-recovery:${this.props.path}`;
        const previous = Number(sessionStorage.getItem(key) || 0);
        if (Date.now() - previous > 120000) { sessionStorage.setItem(key, String(Date.now())); window.location.reload(); }
      } catch { /* Keep the recovery panel when storage is unavailable. */ }
    }
  }
  render() {
    if (!this.state.failed) return this.props.children;
    return <main className="grid min-h-screen place-items-center bg-[var(--canvas)] p-6"><section role="alert" className="surface-card max-w-lg space-y-4 p-7"><h1 className="text-xl font-bold">No pudimos abrir esta sección</h1><p className="text-sm text-[var(--muted)]">La pantalla no terminó de cargar. Puedes recuperar el acceso y continuar desde tu inicio.</p><div className="flex flex-wrap gap-3"><button type="button" className="button-primary" onClick={() => window.location.reload()}>Recuperar pantalla</button><a className="button-secondary" href={this.props.home}>Ir a mi inicio</a></div></section></main>;
  }
}

export function RouteRecoveryBoundary({ children }) {
  const location = useLocation(), { user, accessOptions } = useAuth();
  return <RecoveryBoundary key={location.pathname} path={location.pathname} home={accountHome(user, accessOptions)}>{children}</RecoveryBoundary>;
}

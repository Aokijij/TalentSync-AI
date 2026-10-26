import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";
import { accountHome } from "../utils/accountAccess.js";

export function GuestOnly({ busy = false, destination, children }) {
  const { user, loading, accessOptions } = useAuth();
  if (loading) return <div role="status" className="grid min-h-screen place-items-center text-[var(--muted)]">Validando tu sesión…</div>;
  // Let the submitting form complete its intended welcome/invitation redirect.
  if (user && !busy) return <Navigate to={destination || accountHome(user, accessOptions)} replace />;
  return children;
}

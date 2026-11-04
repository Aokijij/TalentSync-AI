export function requiresAuthenticator(user, options = {}) {
  if (options.mode !== "session" || options.mfa_review || user?.mfa_enabled) return false;
  return user?.role === "company" ? options.company_mfa_required === true : user?.role === "admin" && options.admin_mfa_required === true;
}

export function accountHome(user, options = {}) {
  if (!user) return "/login";
  if (user.registration_pending) return "/completar-cuenta";
  if (user.role === "company") return "/empresa/bienvenida";
  if (requiresAuthenticator(user, options)) return "/seguridad";
  return user.role === "company" ? "/empresa" : user.role === "admin" ? "/admin" : "/candidato";
}

export function requiresAuthenticator(user, options = {}) {
  if (options.mode !== "session" || options.mfa_review || user?.mfa_enabled) return false;
  return user?.role === "company" ? options.company_mfa_required === true : user?.role === "admin" && options.admin_mfa_required === true;
}

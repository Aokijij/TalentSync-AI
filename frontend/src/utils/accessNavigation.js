export const invitationPath = (token) => `/equipo/invitacion?token=${encodeURIComponent(token)}`;

export function invitationTokenFromPath(path) {
  if (typeof path !== "string" || !path.startsWith("/") || path.startsWith("//") || path.includes("\\")) return null;
  const url = new URL(path, "http://local.invalid");
  return url.pathname === "/equipo/invitacion" ? url.searchParams.get("token") : null;
}

export function registrationDestination({ company, invitation, accessOptions }) {
  if (!company) return "/bienvenida";
  if (accessOptions.mode === "session" && accessOptions.company_mfa_required !== false) return `/seguridad${invitation ? `?invitation=${encodeURIComponent(invitation)}` : ""}`;
  return invitation ? invitationPath(invitation) : "/empresa/equipo";
}

export function loginDestination({ company, from, user, accessOptions }) {
  const invitation = company ? invitationTokenFromPath(from) : null;
  if (company && accessOptions.mode === "session" && accessOptions.company_mfa_required !== false && !user.mfa_enabled) return `/seguridad${invitation ? `?invitation=${encodeURIComponent(invitation)}` : ""}`;
  if (invitation) return invitationPath(invitation);
  const local = typeof from === "string" && from.startsWith("/") && !from.startsWith("//") && !from.includes("\\");
  const allowed = local && (company ? from.startsWith("/empresa") : !/^\/(empresa|admin|administracion|equipo)/.test(from));
  return allowed ? from : company ? "/empresa" : "/candidato";
}

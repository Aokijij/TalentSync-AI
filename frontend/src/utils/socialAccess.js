const reasons = {
  expired: "La autorización venció o ya fue utilizada. Empieza un nuevo acceso desde aquí.",
  invalid_state: "No pudimos reconocer este intento. Inicia el acceso de nuevo y complétalo en la misma pestaña.",
  browser_mismatch: "El acceso empezó en otro navegador o dirección. Usa la misma pestaña y dirección de TalentSync durante todo el proceso.",
  cancelled: "No se concedió la autorización. Puedes volver a intentarlo o entrar con tu correo.",
  provider_unavailable: "No pudimos completar la conexión con el proveedor. Inténtalo de nuevo; no necesitas cambiar tu contraseña.",
  provider_configuration: "Este método necesita un ajuste de configuración. Puedes entrar con tu correo mientras se revisa.",
  code_rejected: "El proveedor no pudo validar esta autorización. Inicia un nuevo acceso; no reutilices la página anterior.",
  permissions: "El proveedor no concedió los permisos necesarios para entrar. Puedes autorizar de nuevo o usar tu correo.",
  clock_skew: "La hora del servidor necesita sincronizarse. Puedes entrar con tu correo mientras se revisa.",
  identity_not_verified: "No pudimos validar la respuesta del proveedor. Vuelve a elegir tu cuenta o entra con tu correo.",
};

export function socialFailure(status, reason, provider) {
  const label = provider === "google" ? "Google" : provider === "github" ? "GitHub" : undefined;
  const reasonMessage = Object.hasOwn(reasons, reason) ? reasons[reason] : undefined;
  return {
    provider: label,
    title: status === "existing" ? "Tu cuenta ya existe" : "No pudimos completar tu acceso",
    message: status === "existing" ? "Entra con el método que usaste al crear tu cuenta. Después puedes vincular Google o GitHub desde Seguridad, sin perder tu perfil."
      : status === "unavailable" ? "Este método todavía no está disponible. Puedes entrar con tu correo."
        : reasonMessage || "El acceso no se completó. Puedes intentarlo de nuevo o entrar con tu correo.",
    reference: label && reasonMessage ? `${provider.toUpperCase()} · ${reason.toUpperCase()}` : null,
    retry: status !== "existing" && status !== "unavailable" && reason !== "provider_configuration" && reason !== "clock_skew",
  };
}

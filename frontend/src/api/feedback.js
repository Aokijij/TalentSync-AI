// These POST endpoints calculate, preview, download or maintain presence.
// Successful requests here do not mean that the user's edits were saved.
const transient = [
  /^\/jobs\/\d+\/external-access$/,
  /^\/?auth\//,
  /^\/jobs\/\d+\/match$/,
  /^\/hiring\/(quality\/(preview|writing)|skills\/search)$/,
  /^\/interviews\/rooms\/.*\/(presence|signal|connect)$/,
  /\/(preview|search)$/,
  /^\/profiles\/me\/(export(?:\/preview)?|summary\/generate)$/,
  /^\/recommendations\/me\/(refresh|generate)$/,
  /^\/integrations\/[^/]+\/preview$/,
];
export function shouldNotifyMutation(config = {}) {
  const method = String(config.method || "get").toLowerCase();
  const path = String(config.url || "").split("?")[0];
  return ["post", "put", "patch", "delete"].includes(method) && !config.__quiet && !transient.some((pattern) => pattern.test(path));
}
export function mutationMessage(config = {}, data) {
  if (config.__successMessage) return config.__successMessage;
  if (typeof data?.message === "string" && data.message.trim()) return data.message;
  const method = String(config.method || "get").toLowerCase(), path = String(config.url || "").split("?")[0];
  if (method === "delete") {
    if (path.startsWith("/account/sessions/")) return "Sesión cerrada en ese dispositivo.";
    if (path.startsWith("/account/social-identities/")) return "Acceso social desvinculado.";
    return "Elemento eliminado. La información se ha actualizado.";
  }
  if (path === "/applications") return "Postulación enviada. Puedes consultar su avance en Postulaciones.";
  if (/^\/profiles\/me\/coach\/jobs\/\d+\/cv-versions$/.test(path)) return "Versión del CV guardada. Ya puedes revisarla.";
  if (path === "/profiles/me") return "Perfil actualizado. Tus cambios se han guardado.";
  if (/^\/jobs(?:\/\d+)?$/.test(path)) return method === "post" ? "Vacante creada." : "Vacante actualizada.";
  if (/\/evaluation$/.test(path)) return "Evaluación interna guardada.";
  return ["put", "patch"].includes(method) ? "Cambios guardados correctamente." : "Operación completada.";
}

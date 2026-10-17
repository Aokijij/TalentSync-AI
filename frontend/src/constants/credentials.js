export const DRIVING_CATEGORIES = ["A1", "A2", "B1", "B2", "B3", "C1", "C2", "C3"];
export const CREDENTIAL_STATUSES = { valid: "Vigente", expired: "Vencida", suspended: "Suspendida", in_progress: "En trámite", unknown: "Por confirmar" };
export function credentialStatus(row, today = `${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, "0")}-${String(new Date().getDate()).padStart(2, "0")}`) {
  return row.status === "valid" && row.expires_on && row.expires_on < today ? "Vencida por fecha" : CREDENTIAL_STATUSES[row.status] || "Por confirmar";
}

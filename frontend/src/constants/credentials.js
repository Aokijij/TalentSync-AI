export const DRIVING_CATEGORIES = ["A1", "A2", "B1", "B2", "B3", "C1", "C2", "C3"];
export const CREDENTIAL_STATUSES = { unknown: "Sin indicar", valid: "Vigente", expired: "Vencida", suspended: "Suspendida", in_progress: "En trámite" };

export function credentialStatus(row, today) {
  return row.status === "valid" && row.expires_on && row.expires_on < today ? "Vencida por fecha" : CREDENTIAL_STATUSES[row.status] || "Sin indicar";
}

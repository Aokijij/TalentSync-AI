import { Archive, CheckCircle2 } from "lucide-react";
import { applicationLabels, dashboardDate } from "../utils/dashboardData.js";
import "../styles/application-status-notice.css";

export function ApplicationStatusNotice({ application, compact = false }) {
  const closed = application?.released_at || application?.status === "rejected";
  const Icon = closed ? Archive : CheckCircle2;
  return <div className={`application-status-notice${compact ? " is-compact" : ""}${closed ? " is-closed" : ""}`}>
    <span className="application-status-icon"><Icon size={compact ? 16 : 24} /></span>
    <div><strong>{compact ? application?.released_at ? "Postulación finalizada" : "Postulación enviada" : "Ya te postulaste a esta vacante"}</strong><p>{application?.released_at ? "Proceso cerrado" : applicationLabels[application?.status] || "Registrada en tus postulaciones"}{!compact && application?.created_at && <span>Enviada el {dashboardDate(application.created_at, false)}</span>}</p></div>
  </div>;
}

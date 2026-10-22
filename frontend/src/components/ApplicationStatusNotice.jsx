import { CheckCircle2 } from "lucide-react";
import { applicationLabels, dashboardDate } from "../utils/dashboardData.js";
import "../styles/application-status-notice.css";

export function ApplicationStatusNotice({ application, compact = false }) {
  return <div className={`application-status-notice${compact ? " is-compact" : ""}`}>
    <span className="application-status-icon"><CheckCircle2 size={compact ? 19 : 24} /></span>
    <div><strong>{compact ? "Postulación enviada" : "Ya te postulaste a esta vacante"}</strong><p>{application?.released_at ? "Proceso cerrado" : applicationLabels[application?.status] || "Registrada en tus postulaciones"}{!compact && application?.created_at && <span>Enviada el {dashboardDate(application.created_at, false)}</span>}</p></div>
  </div>;
}
